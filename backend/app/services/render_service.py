import math
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_PAGE_SIZE
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.project import Project
from app.models.render_job import RenderJob, RenderJobStatus
from app.models.user import User
from app.schemas.render import RenderJobListResponse, RenderJobResponse, RenderSubmitRequest


class RenderService:
    def __init__(self, db: Session):
        self.db = db

    def submit_render(self, user: User, data: RenderSubmitRequest) -> RenderJobResponse:
        project = self._get_owned_project(user, data.project_id)

        if not project.composition:
            raise ValidationError("Project has no composition to render")

        job = RenderJob(
            project_id=project.id,
            user_id=user.id,
            status=RenderJobStatus.pending,
            composition_snapshot=dict(project.composition),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        from render_worker.tasks import render_composition_task
        result = render_composition_task.delay(str(job.id))

        job.celery_task_id = result.id
        self.db.commit()
        self.db.refresh(job)

        return RenderJobResponse.model_validate(job)

    def get_render_job(self, user: User, job_id: UUID) -> RenderJobResponse:
        job = self._get_owned_job(user, job_id)
        return RenderJobResponse.model_validate(job)

    def list_render_jobs(
        self,
        user: User,
        project_id: UUID | None,
        page: int,
        page_size: int,
    ) -> RenderJobListResponse:
        query = self.db.query(RenderJob).filter(RenderJob.user_id == user.id)
        if project_id is not None:
            query = query.filter(RenderJob.project_id == project_id)

        total = query.count()
        items = (
            query.order_by(RenderJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return RenderJobListResponse(
            items=[RenderJobResponse.model_validate(j) for j in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def cancel_render_job(self, user: User, job_id: UUID) -> None:
        job = self._get_owned_job(user, job_id)

        if job.status not in (RenderJobStatus.pending, RenderJobStatus.processing):
            raise ValidationError(
                f"Cannot cancel a job with status '{job.status}'"
            )

        if job.celery_task_id:
            from render_worker.worker import celery_app
            celery_app.control.revoke(job.celery_task_id, terminate=True)

        job.status = RenderJobStatus.cancelled
        self.db.commit()

    def _get_owned_project(self, user: User, project_id: UUID) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundError("Project")
        if project.user_id != user.id:
            raise ForbiddenError()
        return project

    def _get_owned_job(self, user: User, job_id: UUID) -> RenderJob:
        job = self.db.query(RenderJob).filter(RenderJob.id == job_id).first()
        if not job:
            raise NotFoundError("RenderJob")
        if job.user_id != user.id:
            raise ForbiddenError()
        return job
