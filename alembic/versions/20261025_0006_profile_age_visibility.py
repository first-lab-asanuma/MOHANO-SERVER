"""add profile age visibility

Revision ID: 20261025_0006
Revises: 20261024_0005
Create Date: 2026-10-25
"""

from alembic import op
import sqlalchemy as sa


revision = "20261025_0006"
down_revision = "20261024_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("age_visible", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("profiles", "age_visible", server_default=None)


def downgrade() -> None:
    op.drop_column("profiles", "age_visible")
