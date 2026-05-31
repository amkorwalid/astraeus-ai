from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_PAGE_SIZE
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.render import RenderJobListResponse, RenderJobResponse, RenderSubmitRequest
from app.services.render_service import RenderService

router = APIRouter(prefix="/renders", tags=["Renders"])


@router.post("", response_model=RenderJobResponse, status_code=201)
def submit_render(
    data: RenderSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RenderService(db).submit_render(current_user, data)


@router.get("", response_model=RenderJobListResponse)
def list_render_jobs(
    project_id: Optional[UUID] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RenderService(db).list_render_jobs(current_user, project_id, page, page_size)


@router.get("/{job_id}", response_model=RenderJobResponse)
def get_render_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return RenderService(db).get_render_job(current_user, job_id)


@router.delete("/{job_id}", status_code=204)
def cancel_render_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    RenderService(db).cancel_render_job(current_user, job_id)
