import hashlib
import hmac
from datetime import date
from typing import Optional

from app.core.errors import ServiceError
from app.core.security import as_utc, utc_now
from app.repositories.matching_repository import MatchExposure, MatchingRepository
from app.schemas.matching import CandidateListResponse, MatchCandidate, MatchPreferences, MatchPreferencesUpdateRequest
from app.services.database_profile_service import DatabaseProfileService


class MatchingService:
    """One-sided preference filtering and repeatable, history-aware discovery."""

    def __init__(
        self,
        repository: MatchingRepository,
        profile_service: DatabaseProfileService,
        daily_order_secret: str,
    ) -> None:
        self._repository = repository
        self._profile_service = profile_service
        self._daily_order_secret = daily_order_secret.encode("utf-8")

    def get_preferences(self, user_id: str) -> MatchPreferences:
        return self._repository.get_preferences(user_id)

    def update_preferences(self, user_id: str, payload: MatchPreferencesUpdateRequest) -> MatchPreferences:
        if payload.age_min is not None and payload.age_max is not None and payload.age_min > payload.age_max:
            raise ServiceError("invalid_age_range", "age_min must not be greater than age_max", 422)
        return self._repository.update_preferences(user_id, MatchPreferences(**payload.model_dump()))

    def list_candidates(self, user_id: str, limit: int, cursor: Optional[str]) -> CandidateListResponse:
        preferences = self.get_preferences(user_id)
        exposures = self._repository.exposures_for(user_id)
        candidates: list[MatchCandidate] = []
        for candidate_id in self._repository.candidate_ids(user_id):
            # Public profiles intentionally omit a hidden age. Matching must
            # still use the private, calculated age stored for that profile.
            matching_profile = self._profile_service.get_profile(candidate_id)
            public_profile = self._profile_service.get_public_profile(candidate_id)
            if self._matches(
                matching_profile.nationality,
                matching_profile.gender,
                matching_profile.age,
                preferences,
            ):
                candidates.append(MatchCandidate(candidate_id=candidate_id, **public_profile.model_dump()))

        today = utc_now().date()
        # A pass is feedback history, not a permanent block. Prefer people this
        # viewer has never received, then the least recently shown people. The
        # daily HMAC key randomizes ties without relying on database ordering.
        candidates.sort(
            key=lambda candidate: self._discovery_sort_key(
                user_id,
                candidate.candidate_id,
                exposures.get(candidate.candidate_id),
                today,
            )
        )
        if cursor:
            cursor_index = next(
                (index for index, candidate in enumerate(candidates) if candidate.candidate_id == cursor),
                None,
            )
            candidates = candidates[cursor_index + 1 :] if cursor_index is not None else []

        page = candidates[:limit]
        self._repository.record_shown(user_id, [candidate.candidate_id for candidate in page])
        return CandidateListResponse(
            items=page,
            # The mobile app deliberately starts a new discovery batch rather
            # than consuming a cursor, so every explicit refresh is re-ranked
            # from the latest exposure history.
            next_cursor=None,
        )

    def pass_candidate(self, user_id: str, candidate_id: str) -> None:
        if not self._repository.pass_candidate(user_id, candidate_id):
            raise ServiceError("candidate_not_found", "Candidate not found", 404)

    def _daily_sort_key(self, user_id: str, candidate_id: str, today: date) -> bytes:
        value = f"{user_id}:{today.isoformat()}:{candidate_id}".encode("utf-8")
        return hmac.new(self._daily_order_secret, value, hashlib.sha256).digest()

    def _discovery_sort_key(
        self,
        user_id: str,
        candidate_id: str,
        exposure: MatchExposure | None,
        today: date,
    ) -> tuple[int, float, bytes]:
        if exposure is None:
            return (0, 0.0, self._daily_sort_key(user_id, candidate_id, today))
        return (
            1,
            as_utc(exposure.last_shown_at).timestamp(),
            self._daily_sort_key(user_id, candidate_id, today),
        )

    @staticmethod
    def _matches(
        nationality: Optional[str], gender: Optional[str], age: Optional[int], preferences: MatchPreferences
    ) -> bool:
        if preferences.country_code and nationality != preferences.country_code:
            return False
        if preferences.gender and gender != preferences.gender:
            return False
        if preferences.age_min is not None and (age is None or age < preferences.age_min):
            return False
        if preferences.age_max is not None and (age is None or age > preferences.age_max):
            return False
        return True
