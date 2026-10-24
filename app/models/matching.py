from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.security import utc_now
from app.db.base import Base


class MatchPreferenceRecord(Base):
    __tablename__ = "match_preferences"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    age_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    age_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class MatchExposureRecord(Base):
    __tablename__ = "match_exposures"

    viewer_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    last_shown_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    passed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CallRequestRecord(Base):
    __tablename__ = "call_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    requester_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class CallSessionRecord(Base):
    __tablename__ = "call_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    call_request_id: Mapped[str] = mapped_column(ForeignKey("call_requests.id", ondelete="CASCADE"), nullable=False, unique=True)
    requester_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="connecting")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class CallSignalRecord(Base):
    __tablename__ = "call_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("call_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(16), nullable=False)
    payload_json: Mapped[str] = mapped_column(String(12000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
