import math
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectSummaryResponse,
    ProjectUpdateRequest,
)
from composition_engine import (
    CompositionValidationError,
    Resolution,
    normalize_composition,
    validate_composition,
)
from composition_engine.schema import Composition
from composition_engine.serializer import composition_from_dict, composition_to_dict


class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, user: User, data: ProjectCreateRequest) -> ProjectResponse:
        empty_comp = Composition(
            resolution=Resolution(width=data.resolution_width, height=data.resolution_height),
            fps=data.fps,
            duration=0.0,
            tracks=[],
        )
        project = Project(
            user_id=user.id,
            name=data.name,
            description=data.description,
            composition=composition_to_dict(empty_comp),
            resolution_width=data.resolution_width,
            resolution_height=data.resolution_height,
            fps=data.fps,
            duration=0.0,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return ProjectResponse.model_validate(project)

    def get_project(self, user: User, project_id: UUID) -> ProjectResponse:
        project = self._get_owned_project(user, project_id)
        return ProjectResponse.model_validate(project)

    def list_projects(
        self,
        user: User,
        archived: bool,
        page: int,
        page_size: int,
    ) -> ProjectListResponse:
        query = self.db.query(Project).filter(
            Project.user_id == user.id,
            Project.is_archived.is_(archived),
        )
        total = query.count()
        items = (
            query.order_by(Project.updated_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return ProjectListResponse(
            items=[ProjectSummaryResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def update_project(self, user: User, project_id: UUID, data: ProjectUpdateRequest) -> ProjectResponse:
        project = self._get_owned_project(user, project_id)

        old_snapshot = dict(project.composition)

        if data.composition is not None:
            try:
                comp = composition_from_dict(data.composition)
                validate_composition(comp)
                comp = normalize_composition(comp)
                new_comp_dict = composition_to_dict(comp)
                project.composition = new_comp_dict
                project.duration = comp.duration
                project.resolution_width = comp.resolution.width
                project.resolution_height = comp.resolution.height
                project.fps = comp.fps
            except CompositionValidationError as exc:
                raise ValidationError(str(exc))

        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        if data.is_archived is not None:
            project.is_archived = data.is_archived
        if data.thumbnail_url is not None:
            project.thumbnail_url = data.thumbnail_url

        # Phase 8 hook: create version snapshot before committing
        try:
            from app.services.project_version_service import ProjectVersionService
            ProjectVersionService(self.db).create_version(project, old_snapshot, user.id)
        except ImportError:
            pass

        self.db.commit()
        self.db.refresh(project)
        return ProjectResponse.model_validate(project)

    def delete_project(self, user: User, project_id: UUID) -> None:
        project = self._get_owned_project(user, project_id)
        self.db.delete(project)
        self.db.commit()

    def _get_owned_project(self, user: User, project_id: UUID) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundError("Project")
        if project.user_id != user.id:
            raise ForbiddenError()
        return project
