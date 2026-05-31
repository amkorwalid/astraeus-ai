import math
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.constants import MAX_VERSIONS_PER_PROJECT
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.schemas.project import ProjectResponse
from app.schemas.project_version import ProjectVersionListResponse, ProjectVersionResponse
from composition_engine.serializer import composition_from_dict


class ProjectVersionService:
    def __init__(self, db: Session):
        self.db = db

    def create_version(
        self,
        project: Project,
        composition_snapshot: dict,
        created_by_user_id: UUID,
    ) -> ProjectVersion:
        next_num = (
            self.db.query(func.max(ProjectVersion.version_number))
            .filter(ProjectVersion.project_id == project.id)
            .scalar()
            or 0
        ) + 1

        version = ProjectVersion(
            project_id=project.id,
            version_number=next_num,
            composition_snapshot=composition_snapshot,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(version)
        self.db.flush()
        self._prune_versions(project.id)
        return version

    def _prune_versions(self, project_id: UUID) -> None:
        count = (
            self.db.query(func.count(ProjectVersion.id))
            .filter(ProjectVersion.project_id == project_id)
            .scalar()
        )
        if count > MAX_VERSIONS_PER_PROJECT:
            to_delete = count - MAX_VERSIONS_PER_PROJECT
            oldest_ids = [
                row.id
                for row in (
                    self.db.query(ProjectVersion.id)
                    .filter(ProjectVersion.project_id == project_id)
                    .order_by(ProjectVersion.version_number.asc())
                    .limit(to_delete)
                    .all()
                )
            ]
            self.db.query(ProjectVersion).filter(
                ProjectVersion.id.in_(oldest_ids)
            ).delete(synchronize_session=False)

    def list_versions(
        self,
        user: User,
        project_id: UUID,
        page: int,
        page_size: int,
    ) -> ProjectVersionListResponse:
        self._get_owned_project(user, project_id)
        query = (
            self.db.query(ProjectVersion)
            .filter(ProjectVersion.project_id == project_id)
            .order_by(ProjectVersion.version_number.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return ProjectVersionListResponse(
            items=[ProjectVersionResponse.model_validate(v) for v in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def restore_version(
        self,
        user: User,
        project_id: UUID,
        version_id: UUID,
    ) -> ProjectResponse:
        project = self._get_owned_project(user, project_id)

        version = (
            self.db.query(ProjectVersion)
            .filter(
                ProjectVersion.id == version_id,
                ProjectVersion.project_id == project_id,
            )
            .first()
        )
        if not version:
            raise NotFoundError("ProjectVersion")

        # Snapshot the current state before restoring (so restore is undoable)
        current_snapshot = dict(project.composition)
        self.create_version(project, current_snapshot, user.id)

        # Apply the target snapshot
        restored_comp = composition_from_dict(dict(version.composition_snapshot))
        project.composition = dict(version.composition_snapshot)
        project.duration = restored_comp.duration
        project.resolution_width = restored_comp.resolution.width
        project.resolution_height = restored_comp.resolution.height
        project.fps = restored_comp.fps

        self.db.commit()
        self.db.refresh(project)

        from app.schemas.project import ProjectResponse
        return ProjectResponse.model_validate(project)

    def _get_owned_project(self, user: User, project_id: UUID) -> Project:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise NotFoundError("Project")
        if project.user_id != user.id:
            raise ForbiddenError()
        return project
