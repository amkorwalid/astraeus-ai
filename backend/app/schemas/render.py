from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.render_job import RenderJobStatus


class RenderSubmitRequest(BaseModel):
    project_id: UUID


class RenderJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    user_id: UUID
    status: RenderJobStatus
    progress: float
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    celery_task_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RenderJobListResponse(BaseModel):
    items: list[RenderJobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
