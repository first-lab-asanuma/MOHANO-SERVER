from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import utc_now
from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(30), nullable=False, default="New friend")
    nationality: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    age_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mbti: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    introduction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    languages: Mapped[list["ProfileLanguage"]] = relationship(cascade="all, delete-orphan", order_by="ProfileLanguage.language_code")
    interests: Mapped[list["ProfileInterest"]] = relationship(cascade="all, delete-orphan", order_by="ProfileInterest.interest_code")
    photos: Mapped[list["ProfilePhotoRecord"]] = relationship(cascade="all, delete-orphan", order_by="ProfilePhotoRecord.position")


class ProfileLanguage(Base):
    __tablename__ = "profile_languages"

    user_id: Mapped[str] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(8), primary_key=True)


class ProfileInterest(Base):
    __tablename__ = "profile_interests"

    user_id: Mapped[str] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True)
    interest_code: Mapped[str] = mapped_column(String(64), primary_key=True)


class ProfilePhotoRecord(Base):
    __tablename__ = "profile_photos"
    __table_args__ = (UniqueConstraint("user_id", "position", name="uq_profile_photo_position"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("profiles.user_id", ondelete="CASCADE"), nullable=False, index=True)
    image_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
