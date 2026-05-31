"""Add media table

Revision ID: 002
Revises: 001
Create Date: 2026-05-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE media_type AS ENUM ('video', 'audio', 'image')")
    op.execute("CREATE TYPE media_status AS ENUM ('uploading', 'processing', 'ready', 'failed')")

    op.create_table(
        "media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column(
            "media_type",
            sa.Enum("video", "audio", "image", name="media_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("uploading", "processing", "ready", "failed", name="media_status", create_type=False),
            nullable=False,
            server_default="uploading",
        ),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_url", sa.String(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("fps", sa.Float(), nullable=True),
        sa.Column("bitrate", sa.Integer(), nullable=True),
        sa.Column("codec", sa.String(50), nullable=True),
        sa.Column("thumbnail_url", sa.String(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_media_user_id", "media", ["user_id"])
    op.create_index("ix_media_storage_key", "media", ["storage_key"], unique=True)
    op.create_index("ix_media_user_type", "media", ["user_id", "media_type"])
    op.create_index("ix_media_user_status", "media", ["user_id", "status"])


def downgrade() -> None:
    op.drop_table("media")
    op.execute("DROP TYPE media_status")
    op.execute("DROP TYPE media_type")
