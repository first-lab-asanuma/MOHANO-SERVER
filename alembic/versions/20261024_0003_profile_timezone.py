"""add IANA timezone to profiles

Revision ID: 20261024_0003
Revises: 20261023_0002
Create Date: 2026-10-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20261024_0003"
down_revision = "20261023_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("timezone", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("profiles", "timezone")
