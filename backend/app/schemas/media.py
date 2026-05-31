from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.models.media import MediaType, MediaStatus


class UploadUrlRequest(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int


class UploadUrlResponse(BaseModel):
    upload_url: str
    storage_key: str
    expires_at: datetime


class ConfirmUploadRequest(BaseModel):
    storage_key: str
    filename: str
    mime_type: str
    size_bytes: int


class MediaResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    storage_key: str
    filename: str
    original_filename: str
    mime_type: str
    media_type: MediaType
    status: MediaStatus
    size_bytes: int
    storage_url: str
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime


class MediaListResponse(BaseModel):
    items: list[MediaResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
