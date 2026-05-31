import json
import math
import re
import subprocess
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.media import Media, MediaStatus, MediaType
from app.models.user import User
from app.schemas.media import (
    ConfirmUploadRequest,
    MediaListResponse,
    MediaResponse,
    UploadUrlRequest,
    UploadUrlResponse,
)

_MIME_TYPE_MAP = {
    "video/": MediaType.video,
    "audio/": MediaType.audio,
    "image/": MediaType.image,
}


def _infer_media_type(mime_type: str) -> MediaType:
    for prefix, media_type in _MIME_TYPE_MAP.items():
        if mime_type.startswith(prefix):
            return media_type
    return MediaType.video


def _safe_filename(filename: str) -> str:
    return re.sub(r"[^\w.\-]", "_", filename)


class MediaService:
    def __init__(self, db: Session):
        self.db = db

    def _get_spaces_client(self):
        import boto3
        return boto3.client(
            "s3",
            region_name=settings.DO_SPACES_REGION,
            endpoint_url=settings.DO_SPACES_ENDPOINT,
            aws_access_key_id=settings.DO_SPACES_KEY,
            aws_secret_access_key=settings.DO_SPACES_SECRET,
        )

    def generate_upload_url(self, user: User, data: UploadUrlRequest) -> UploadUrlResponse:
        safe_name = _safe_filename(data.filename)
        storage_key = f"media/{user.id}/{uuid.uuid4()}/{safe_name}"
        expires_in = 900  # 15 minutes

        client = self._get_spaces_client()
        upload_url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.DO_SPACES_BUCKET,
                "Key": storage_key,
                "ContentType": data.mime_type,
            },
            ExpiresIn=expires_in,
        )

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return UploadUrlResponse(
            upload_url=upload_url,
            storage_key=storage_key,
            expires_at=expires_at,
        )

    def confirm_upload(self, user: User, data: ConfirmUploadRequest) -> MediaResponse:
        expected_prefix = f"media/{user.id}/"
        if not data.storage_key.startswith(expected_prefix):
            raise ForbiddenError("Storage key does not belong to this user")

        existing = (
            self.db.query(Media)
            .filter(Media.storage_key == data.storage_key, Media.is_deleted.is_(False))
            .first()
        )
        if existing:
            raise ConflictError("Media with this storage key already exists")

        media_type = _infer_media_type(data.mime_type)
        metadata = self._extract_ffprobe_metadata(data.storage_key)
        storage_url = f"{settings.DO_SPACES_ENDPOINT}/{settings.DO_SPACES_BUCKET}/{data.storage_key}"

        media = Media(
            user_id=user.id,
            storage_key=data.storage_key,
            filename=data.filename,
            original_filename=data.filename,
            mime_type=data.mime_type,
            media_type=media_type,
            status=MediaStatus.ready,
            size_bytes=data.size_bytes,
            storage_url=storage_url,
            duration_seconds=metadata.get("duration_seconds"),
            width=metadata.get("width"),
            height=metadata.get("height"),
            fps=metadata.get("fps"),
            bitrate=metadata.get("bitrate"),
            codec=metadata.get("codec"),
        )
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)
        return MediaResponse.model_validate(media)

    def list_media(
        self,
        user: User,
        media_type: Optional[MediaType],
        page: int,
        page_size: int,
    ) -> MediaListResponse:
        query = self.db.query(Media).filter(
            Media.user_id == user.id,
            Media.is_deleted.is_(False),
        )
        if media_type is not None:
            query = query.filter(Media.media_type == media_type)

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return MediaListResponse(
            items=[MediaResponse.model_validate(m) for m in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_media(self, user: User, media_id: UUID) -> MediaResponse:
        media = self._get_owned_media(user, media_id)
        return MediaResponse.model_validate(media)

    def delete_media(self, user: User, media_id: UUID) -> None:
        media = self._get_owned_media(user, media_id)
        try:
            client = self._get_spaces_client()
            client.delete_object(Bucket=settings.DO_SPACES_BUCKET, Key=media.storage_key)
        except Exception:
            pass
        media.is_deleted = True
        self.db.commit()

    def _get_owned_media(self, user: User, media_id: UUID) -> Media:
        media = (
            self.db.query(Media)
            .filter(Media.id == media_id, Media.is_deleted.is_(False))
            .first()
        )
        if not media:
            raise NotFoundError("Media")
        if media.user_id != user.id:
            raise NotFoundError("Media")
        return media

    def _extract_ffprobe_metadata(self, storage_key: str) -> dict:
        try:
            url = f"{settings.DO_SPACES_ENDPOINT}/{settings.DO_SPACES_BUCKET}/{storage_key}"
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_streams",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            metadata = {}
            for stream in streams:
                if stream.get("codec_type") == "video":
                    metadata["width"] = stream.get("width")
                    metadata["height"] = stream.get("height")
                    metadata["codec"] = stream.get("codec_name")
                    raw_fps = stream.get("r_frame_rate", "0/1")
                    num, den = (int(x) for x in raw_fps.split("/"))
                    metadata["fps"] = num / den if den else 0
                    duration = stream.get("duration")
                    if duration:
                        metadata["duration_seconds"] = float(duration)
                    bitrate = stream.get("bit_rate")
                    if bitrate:
                        metadata["bitrate"] = int(bitrate)
                    break
                if stream.get("codec_type") == "audio" and "duration_seconds" not in metadata:
                    duration = stream.get("duration")
                    if duration:
                        metadata["duration_seconds"] = float(duration)
            return metadata
        except Exception:
            return {}
