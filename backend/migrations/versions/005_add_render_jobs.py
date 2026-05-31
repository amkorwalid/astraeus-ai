"""Add render_jobs table

Revision ID: 005
Revises: 004
Create Date: 2026-05-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE render_job_status AS ENUM "
        "('pending', 'processing', 'completed', 'failed', 'cancelled')"
    )
    op.create_table(
        "render_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "processing", "completed", "failed", "cancelled",
                name="render_job_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("composition_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("output_url", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index("ix_render_jobs_project_id", "render_jobs", ["project_id"])
    op.create_index("ix_render_jobs_user_id", "render_jobs", ["user_id"])
    op.create_index("ix_render_jobs_status", "render_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("render_jobs")
    op.execute("DROP TYPE IF EXISTS render_job_status")
