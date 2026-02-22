"""Initial schema - all 6 tables

Revision ID: 001_initial
Revises:
Create Date: 2026-02-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("phone", sa.String(20), unique=True, nullable=False, index=True),
        sa.Column("nickname", sa.String(128), nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "ai_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("encrypted_api_key", sa.Text, nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "batches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(20), server_default="uploading", nullable=False),
        sa.Column("total_photos", sa.Integer, server_default="0"),
        sa.Column("uploaded_photos", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "photos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("batch_id", UUID(as_uuid=True), sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("thumbnail_path", sa.String(512), nullable=True),
        sa.Column("compressed_path", sa.String(512), nullable=True),
        sa.Column("mime_type", sa.String(50), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("width", sa.Integer, nullable=True),
        sa.Column("height", sa.Integer, nullable=True),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("camera_model", sa.String(128), nullable=True),
        sa.Column("gps_latitude", sa.Float, nullable=True),
        sa.Column("gps_longitude", sa.Float, nullable=True),
        sa.Column("orientation", sa.Integer, nullable=True),
        sa.Column("phash", sa.String(64), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "photo_analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("photo_id", UUID(as_uuid=True), sa.ForeignKey("photos.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("sub_category", sa.String(50), nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("quality_score", sa.Float, nullable=True),
        sa.Column("is_blurry", sa.Boolean, server_default=sa.text("false")),
        sa.Column("is_overexposed", sa.Boolean, server_default=sa.text("false")),
        sa.Column("is_underexposed", sa.Boolean, server_default=sa.text("false")),
        sa.Column("is_screenshot", sa.Boolean, server_default=sa.text("false")),
        sa.Column("is_invalid", sa.Boolean, server_default=sa.text("false")),
        sa.Column("invalid_reason", sa.String(255), nullable=True),
        sa.Column("similarity_group", sa.String(64), nullable=True, index=True),
        sa.Column("is_best_in_group", sa.Boolean, server_default=sa.text("false")),
        sa.Column("ai_provider", sa.String(50), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "processing_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("batch_id", UUID(as_uuid=True), sa.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("current_stage", sa.Integer, server_default="0"),
        sa.Column("total_stages", sa.Integer, server_default="5"),
        sa.Column("current_stage_name", sa.String(50), nullable=True),
        sa.Column("progress_percent", sa.Integer, server_default="0"),
        sa.Column("photos_processed", sa.Integer, server_default="0"),
        sa.Column("photos_total", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("processing_tasks")
    op.drop_table("photo_analyses")
    op.drop_table("photos")
    op.drop_table("batches")
    op.drop_table("ai_configs")
    op.drop_table("users")
