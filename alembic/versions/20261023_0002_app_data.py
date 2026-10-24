"""add profile matching call and chat tables

Revision ID: 20261023_0002
Revises: 20261023_0001
Create Date: 2026-10-23
"""
from alembic import op
import sqlalchemy as sa

revision = "20261023_0002"
down_revision = "20261023_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("nickname", sa.String(length=30), nullable=False),
        sa.Column("nationality", sa.String(length=2), nullable=True),
        sa.Column("gender", sa.String(length=24), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("mbti", sa.String(length=4), nullable=True),
        sa.Column("introduction", sa.Text(), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table("profile_languages", sa.Column("user_id", sa.String(length=36), nullable=False), sa.Column("language_code", sa.String(length=8), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["profiles.user_id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("user_id", "language_code"))
    op.create_table("profile_interests", sa.Column("user_id", sa.String(length=36), nullable=False), sa.Column("interest_code", sa.String(length=64), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["profiles.user_id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("user_id", "interest_code"))
    op.create_table("profile_photos", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("user_id", sa.String(length=36), nullable=False), sa.Column("image_ref", sa.String(length=500), nullable=False), sa.Column("position", sa.Integer(), nullable=False), sa.Column("is_primary", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["profiles.user_id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("user_id", "position", name="uq_profile_photo_position"))
    op.create_index("ix_profile_photos_user_id", "profile_photos", ["user_id"])
    op.create_table("match_preferences", sa.Column("user_id", sa.String(length=36), nullable=False), sa.Column("country_code", sa.String(length=2), nullable=True), sa.Column("gender", sa.String(length=24), nullable=True), sa.Column("age_min", sa.Integer(), nullable=True), sa.Column("age_max", sa.Integer(), nullable=True), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("user_id"))
    op.create_table("call_requests", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("requester_id", sa.String(length=36), nullable=False), sa.Column("recipient_id", sa.String(length=36), nullable=False), sa.Column("status", sa.String(length=16), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_call_requests_requester_id", "call_requests", ["requester_id"])
    op.create_index("ix_call_requests_recipient_id", "call_requests", ["recipient_id"])
    op.create_table("call_sessions", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("call_request_id", sa.String(length=36), nullable=False), sa.Column("requester_id", sa.String(length=36), nullable=False), sa.Column("recipient_id", sa.String(length=36), nullable=False), sa.Column("status", sa.String(length=16), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["call_request_id"], ["call_requests.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("call_request_id"))
    op.create_index("ix_call_sessions_requester_id", "call_sessions", ["requester_id"])
    op.create_index("ix_call_sessions_recipient_id", "call_sessions", ["recipient_id"])
    op.create_table("call_signals", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("session_id", sa.String(length=36), nullable=False), sa.Column("sender_id", sa.String(length=36), nullable=False), sa.Column("signal_type", sa.String(length=16), nullable=False), sa.Column("payload_json", sa.String(length=12000), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["session_id"], ["call_sessions.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_call_signals_session_id", "call_signals", ["session_id"])
    op.create_index("ix_call_signals_sender_id", "call_signals", ["sender_id"])
    op.create_table("conversations", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.PrimaryKeyConstraint("id"))
    op.create_table("conversation_members", sa.Column("conversation_id", sa.String(length=36), nullable=False), sa.Column("user_id", sa.String(length=36), nullable=False), sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True), sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("conversation_id", "user_id"))
    op.create_table("messages", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("conversation_id", sa.String(length=36), nullable=False), sa.Column("sender_id", sa.String(length=36), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_sender_id", "messages", ["sender_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])


def downgrade() -> None:
    for index, table in (("ix_messages_created_at", "messages"), ("ix_messages_sender_id", "messages"), ("ix_messages_conversation_id", "messages")):
        op.drop_index(index, table_name=table)
    op.drop_table("messages")
    op.drop_table("conversation_members")
    op.drop_table("conversations")
    for index, table in (("ix_call_signals_sender_id", "call_signals"), ("ix_call_signals_session_id", "call_signals")):
        op.drop_index(index, table_name=table)
    op.drop_table("call_signals")
    op.drop_index("ix_call_sessions_recipient_id", table_name="call_sessions")
    op.drop_index("ix_call_sessions_requester_id", table_name="call_sessions")
    op.drop_table("call_sessions")
    op.drop_index("ix_call_requests_recipient_id", table_name="call_requests")
    op.drop_index("ix_call_requests_requester_id", table_name="call_requests")
    op.drop_table("call_requests")
    op.drop_table("match_preferences")
    op.drop_index("ix_profile_photos_user_id", table_name="profile_photos")
    op.drop_table("profile_photos")
    op.drop_table("profile_interests")
    op.drop_table("profile_languages")
    op.drop_table("profiles")
