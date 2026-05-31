import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, Boolean, Integer, Float, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    composition = Column(JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"))
    resolution_width = Column(Integer, nullable=False, default=1920)
    resolution_height = Column(Integer, nullable=False, default=1080)
    fps = Column(Integer, nullable=False, default=30)
    duration = Column(Float, nullable=False, default=0.0)
    is_archived = Column(Boolean, default=False, nullable=False)
    thumbnail_url = Column(String, nullable=True)

    user = relationship("User", back_populates="projects")
    versions = relationship("ProjectVersion", back_populates="project", cascade="all, delete-orphan")
    media_associations = relationship("ProjectMedia", back_populates="project", cascade="all, delete-orphan")


class ProjectMedia(Base):
    __tablename__ = "project_media"

    __table_args__ = (
        UniqueConstraint("project_id", "media_id", name="uq_project_media_project_media"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    media_id = Column(
        UUID(as_uuid=True),
        ForeignKey("media.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    added_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="media_associations")
    media = relationship("Media")
