from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_PAGE_SIZE
from app.database import get_db
from app.dependencies import get_current_user
from app.models.media import MediaType
from app.models.user import User
from app.schemas.media import (
    ConfirmUploadRequest,
    MediaListResponse,
    MediaResponse,
    UploadUrlRequest,
    UploadUrlResponse,
)
from app.services.media_service import MediaService

router = APIRouter(prefix="/media", tags=["Media"])


@router.post("/upload-url", response_model=UploadUrlResponse)
def request_upload_url(
    data: UploadUrlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MediaService(db).generate_upload_url(current_user, data)


@router.post("/confirm", response_model=MediaResponse, status_code=201)
def confirm_upload(
    data: ConfirmUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MediaService(db).confirm_upload(current_user, data)


@router.get("", response_model=MediaListResponse)
def list_media(
    media_type: Optional[MediaType] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MediaService(db).list_media(current_user, media_type, page, page_size)


@router.get("/{media_id}", response_model=MediaResponse)
def get_media(
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return MediaService(db).get_media(current_user, media_id)


@router.delete("/{media_id}", status_code=204)
def delete_media(
    media_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    MediaService(db).delete_media(current_user, media_id)
