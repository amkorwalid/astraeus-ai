import uuid
import enum
from sqlalchemy import Column, String, Boolean, Integer, Float, Enum, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class MediaType(str, enum.Enum):
    video = "video"
    audio = "audio"
    image = "image"


class MediaStatus(str, enum.Enum):
    uploading = "uploading"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Media(Base, TimestampMixin):
    __tablename__ = "media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    storage_key = Column(String(500), unique=True, nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    media_type = Column(Enum(MediaType, name="media_type"), nullable=False)
    status = Column(
        Enum(MediaStatus, name="media_status"),
        nullable=False,
        default=MediaStatus.uploading,
    )
    size_bytes = Column(BigInteger, nullable=False)
    storage_url = Column(String, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    bitrate = Column(Integer, nullable=True)
    codec = Column(String(50), nullable=True)
    thumbnail_url = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="media")
