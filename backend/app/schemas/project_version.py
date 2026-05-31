from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel


class ProjectVersionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    project_id: UUID
    version_number: int
    composition_snapshot: dict[str, Any]
    created_by_user_id: Optional[UUID] = None
    change_summary: Optional[str] = None
    created_at: datetime


class ProjectVersionListResponse(BaseModel):
    items: list[ProjectVersionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
