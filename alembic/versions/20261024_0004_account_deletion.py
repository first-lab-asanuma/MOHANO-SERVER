"""add logical account deletion audit fields

Revision ID: 20261024_0004
Revises: 20261024_0003
Create Date: 2026-10-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20261024_0004"
down_revision = "20261024_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "deleted_at")
