from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.profile import PublicProfile


class MatchPreferences(BaseModel):
    country_code: Optional[str] = Field(default=None, min_length=2, max_length=2)
    gender: Optional[str] = None
    age_min: Optional[int] = Field(default=None, ge=18, le=99)
    age_max: Optional[int] = Field(default=None, ge=18, le=99)


class MatchPreferencesUpdateRequest(MatchPreferences):
    pass


class MatchCandidate(PublicProfile):
    candidate_id: str


class CandidateListResponse(BaseModel):
    items: list[MatchCandidate]
    next_cursor: Optional[str] = None
