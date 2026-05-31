from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    resolution_width: int = 1920
    resolution_height: int = 1080
    fps: int = 30


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    composition: Optional[dict[str, Any]] = None
    is_archived: Optional[bool] = None
    thumbnail_url: Optional[str] = None


class ProjectSummaryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    resolution_width: int
    resolution_height: int
    fps: int
    duration: float
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class ProjectResponse(ProjectSummaryResponse):
    composition: dict[str, Any]


class ProjectListResponse(BaseModel):
    items: list[ProjectSummaryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
