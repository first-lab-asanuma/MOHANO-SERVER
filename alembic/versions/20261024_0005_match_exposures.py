"""add discovery exposure and pass history

Revision ID: 20261024_0005
Revises: 20261024_0004
Create Date: 2026-10-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20261024_0005"
down_revision = "20261024_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "match_exposures",
        sa.Column("viewer_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_id", sa.String(length=36), nullable=False),
        sa.Column("last_shown_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("passed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["viewer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("viewer_id", "candidate_id"),
    )
    op.create_index("ix_match_exposures_viewer_passed", "match_exposures", ["viewer_id", "passed_at"])


def downgrade() -> None:
    op.drop_index("ix_match_exposures_viewer_passed", table_name="match_exposures")
    op.drop_table("match_exposures")
