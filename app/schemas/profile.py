from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ProfilePhoto(BaseModel):
    photo_id: str
    image_url: str
    position: int
    is_primary: bool


class PublicProfile(BaseModel):
    nickname: str
    nationality: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    age_visible: bool = True
    languages: List[str] = Field(default_factory=list)
    mbti: Optional[str] = None
    interest_codes: List[str] = Field(default_factory=list)
    introduction: Optional[str] = None
    primary_photo: Optional[ProfilePhoto] = None


class ProfileResponse(PublicProfile):
    user_id: str
    birth_date: Optional[date] = None
    timezone: Optional[str] = None
    photos: List[ProfilePhoto] = Field(default_factory=list)
    onboarding_completed: bool = False


class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(default=None, min_length=1, max_length=20)
    nationality: Optional[str] = Field(default=None, pattern=r"^[A-Z]{2}$")
    gender: Optional[Literal["man", "woman", "non_binary"]] = None
    birth_date: Optional[date] = None
    age_visible: Optional[bool] = None
    timezone: Optional[str] = Field(default=None, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_+/-]+$")
    languages: Optional[List[str]] = Field(default=None, min_length=1, max_length=3)
    mbti: Optional[str] = Field(default=None, pattern=r"^(INTJ|INTP|ENTJ|ENTP|INFJ|INFP|ENFJ|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ISTP|ISFP|ESTP|ESFP)$")
    interest_codes: Optional[List[str]] = Field(default=None, min_length=3, max_length=5)
    introduction: Optional[str] = Field(default=None, max_length=180)


class ProfilePhotoCreateRequest(BaseModel):
    """Legacy mock-only request retained until mock services are removed."""

    image_ref: str = Field(min_length=1, max_length=500)
    is_primary: bool = False


class ProfilePhotoUploadRequest(BaseModel):
    content_type: str = Field(min_length=1, max_length=100)
    content_length: int = Field(gt=0, le=10 * 1024 * 1024)


class ProfilePhotoUploadUrl(BaseModel):
    upload_id: str
    upload_url: str
    content_type: str
    expires_in_seconds: int
