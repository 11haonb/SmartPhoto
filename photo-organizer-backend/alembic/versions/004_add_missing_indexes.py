"""Add missing indexes for photos and user_selections

Revision ID: 004_add_missing_indexes
Revises: 003_add_composite_indexes
Create Date: 2026-02-25

"""
from alembic import op

revision = "004_add_missing_indexes"
down_revision = "003_add_composite_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Speed up per-user photo queries
    op.create_index(
        "ix_photos_user_id",
        "photos",
        ["user_id"],
        if_not_exists=True,
    )
    # Speed up user_selections lookups
    op.create_index(
        "ix_user_selections_user_task",
        "user_selections",
        ["user_id", "task_id"],
        if_not_exists=True,
    )
    # Speed up similarity group lookups in user_selections
    op.create_index(
        "ix_user_selections_group",
        "user_selections",
        ["similarity_group"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_user_selections_group", table_name="user_selections", if_exists=True)
    op.drop_index("ix_user_selections_user_task", table_name="user_selections", if_exists=True)
    op.drop_index("ix_photos_user_id", table_name="photos", if_exists=True)
