import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from render_worker.worker import celery_app


@celery_app.task(name="render_worker.tasks.render_composition_task", bind=True)
def render_composition_task(self, job_id: str) -> dict:
    from app.database import SessionLocal
    from app.models.render_job import RenderJob, RenderJobStatus
    from composition_engine.serializer import composition_from_dict
    from render_worker.executor import FFmpegError, FFmpegExecutor
    from render_worker.filter_graph import FilterGraphBuilder
    from render_worker.parser import collect_media_srcs, download_media_files, parse_composition
    from render_worker.progress import make_progress_callback

    db = SessionLocal()
    job = None
    work_dir = f"/tmp/astraeus_render/{job_id}"

    try:
        job = db.query(RenderJob).filter(RenderJob.id == job_id).first()
        if not job:
            return {"error": f"Job {job_id} not found"}

        job.status = RenderJobStatus.processing
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        Path(work_dir).mkdir(parents=True, exist_ok=True)
        output_path = os.path.join(work_dir, "output.mp4")

        comp = composition_from_dict(job.composition_snapshot)
        plan = parse_composition(comp, work_dir=work_dir)

        srcs = collect_media_srcs(plan)
        cache_dir = "/tmp/astraeus_cache"
        input_files = download_media_files(srcs, cache_dir=cache_dir)

        cmd = FilterGraphBuilder().build_command(plan, output_path, input_files)

        last_db_update = time.monotonic()

        def on_progress(pct: float) -> None:
            nonlocal last_db_update
            now = time.monotonic()
            if now - last_db_update >= 2.0:
                job.progress = pct
                db.commit()
                last_db_update = now

        progress_cb = make_progress_callback(comp.duration, on_progress)
        FFmpegExecutor().run(cmd, on_stderr_line=progress_cb)

        output_url = _upload_output(job_id, output_path)

        job.status = RenderJobStatus.completed
        job.progress = 100.0
        job.output_url = output_url
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

        return {"status": "completed", "output_url": output_url}

    except FFmpegError as exc:
        if job:
            job.status = RenderJobStatus.failed
            job.error_message = f"FFmpeg error (code {exc.returncode}): {exc.stderr[-300:]}"
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise

    except Exception as exc:
        if job:
            job.status = RenderJobStatus.failed
            job.error_message = str(exc)[:1000]
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise

    finally:
        db.close()
        _cleanup_work_dir(work_dir)


def _upload_output(job_id: str, output_path: str) -> str:
    import boto3
    from app.config import settings

    storage_key = f"renders/{job_id}/output.mp4"
    client = boto3.client(
        "s3",
        region_name=settings.DO_SPACES_REGION,
        endpoint_url=settings.DO_SPACES_ENDPOINT,
        aws_access_key_id=settings.DO_SPACES_KEY,
        aws_secret_access_key=settings.DO_SPACES_SECRET,
    )
    client.upload_file(
        output_path,
        settings.DO_SPACES_BUCKET,
        storage_key,
        ExtraArgs={"ACL": "public-read", "ContentType": "video/mp4"},
    )
    return f"{settings.DO_SPACES_ENDPOINT}/{settings.DO_SPACES_BUCKET}/{storage_key}"


def _cleanup_work_dir(work_dir: str) -> None:
    import shutil
    try:
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception:
        pass
