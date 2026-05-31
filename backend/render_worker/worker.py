from celery import Celery
from app.config import settings

celery_app = Celery(
    "render_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

celery_app.autodiscover_tasks(["render_worker"])


@celery_app.task(name="render_worker.worker.ping_task")
def ping_task() -> str:
    return "pong"
