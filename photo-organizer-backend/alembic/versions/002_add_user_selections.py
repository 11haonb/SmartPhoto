"""Add user_selections table

Revision ID: 002_add_user_selections
Revises: 001_initial
Create Date: 2026-02-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "002_add_user_selections"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_selections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("photo_id", UUID(as_uuid=True), sa.ForeignKey("photos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("similarity_group", sa.String(64), nullable=False),
        sa.Column("task_id", UUID(as_uuid=True), sa.ForeignKey("processing_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("selected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "similarity_group", "task_id", name="uq_user_group_task"),
    )
    op.create_index("ix_user_selections_user_task", "user_selections", ["user_id", "task_id"])


def downgrade() -> None:
    op.drop_index("ix_user_selections_user_task", table_name="user_selections")
    op.drop_table("user_selections")
