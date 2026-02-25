"""Add composite indexes for performance

Revision ID: 003_add_composite_indexes
Revises: 002_add_user_selections
Create Date: 2026-02-25

"""
from alembic import op

revision = "003_add_composite_indexes"
down_revision = "002_add_user_selections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Speed up best-photo queries
    op.create_index(
        "ix_photo_analyses_group_best",
        "photo_analyses",
        ["similarity_group", "is_best_in_group"],
    )
    # Speed up batch status queries per user
    op.create_index(
        "ix_batches_user_status",
        "batches",
        ["user_id", "status"],
    )
    # Speed up task lookups per user
    op.create_index(
        "ix_processing_tasks_user_status",
        "processing_tasks",
        ["user_id", "status"],
    )
    # Speed up photo date-range queries
    op.create_index(
        "ix_photos_taken_at",
        "photos",
        ["taken_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_photos_taken_at", table_name="photos")
    op.drop_index("ix_processing_tasks_user_status", table_name="processing_tasks")
    op.drop_index("ix_batches_user_status", table_name="batches")
    op.drop_index("ix_photo_analyses_group_best", table_name="photo_analyses")
