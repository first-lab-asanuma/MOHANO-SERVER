"""add user availability and call notification state

Revision ID: 20261025_0007
Revises: 20261025_0006
Create Date: 2026-10-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20261025_0007"
down_revision = "20261025_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users",
        sa.Column("call_notifications_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("users", sa.Column("push_token", sa.Text(), nullable=True))
    op.create_index("ix_users_last_active_at", "users", ["last_active_at"])
    op.alter_column("users", "call_notifications_enabled", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_users_last_active_at", table_name="users")
    op.drop_column("users", "push_token")
    op.drop_column("users", "call_notifications_enabled")
    op.drop_column("users", "last_active_at")
