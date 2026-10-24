from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user_id
from app.schemas.matching import CandidateListResponse, MatchPreferences, MatchPreferencesUpdateRequest
from app.services.container import get_matching_service
from app.services.matching_service import MatchingService

router = APIRouter()


@router.get("/me/match-preferences", response_model=MatchPreferences)
def get_match_preferences(
    user_id: str = Depends(get_current_user_id),
    service: MatchingService = Depends(get_matching_service),
) -> MatchPreferences:
    return service.get_preferences(user_id)


@router.put("/me/match-preferences", response_model=MatchPreferences)
def update_match_preferences(
    payload: MatchPreferencesUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    service: MatchingService = Depends(get_matching_service),
) -> MatchPreferences:
    return service.update_preferences(user_id, payload)


@router.get("/matches/candidates", response_model=CandidateListResponse)
def list_match_candidates(
    limit: int = Query(default=10, ge=1, le=10),
    cursor: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    service: MatchingService = Depends(get_matching_service),
) -> CandidateListResponse:
    return service.list_candidates(user_id, limit, cursor)


@router.post("/matches/candidates/{candidate_id}/pass", status_code=204)
def pass_match_candidate(
    candidate_id: str,
    user_id: str = Depends(get_current_user_id),
    service: MatchingService = Depends(get_matching_service),
) -> None:
    service.pass_candidate(user_id, candidate_id)
