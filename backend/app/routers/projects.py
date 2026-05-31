from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_PAGE_SIZE
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.schemas.project_version import ProjectVersionListResponse
from app.services.project_service import ProjectService
from app.services.project_version_service import ProjectVersionService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectService(db).create_project(current_user, data)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    archived: bool = False,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectService(db).list_projects(current_user, archived, page, page_size)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectService(db).get_project(current_user, project_id)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    data: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectService(db).update_project(current_user, project_id, data)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ProjectService(db).delete_project(current_user, project_id)


@router.get("/{project_id}/versions", response_model=ProjectVersionListResponse)
def list_versions(
    project_id: UUID,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectVersionService(db).list_versions(current_user, project_id, page, page_size)


@router.post("/{project_id}/versions/{version_id}/restore", response_model=ProjectResponse)
def restore_version(
    project_id: UUID,
    version_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ProjectVersionService(db).restore_version(current_user, project_id, version_id)
