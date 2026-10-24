from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from app.core.security import utc_now
from app.db.session import SessionLocal
from app.models.matching import MatchExposureRecord, MatchPreferenceRecord
from app.models.profile import Profile
from app.models.user import User
from app.repositories.availability_repository import AvailabilityRepository
from app.schemas.matching import MatchPreferences


@dataclass(frozen=True)
class MatchExposure:
    last_shown_at: datetime
    passed_at: datetime | None


class MatchingRepository:
    """MySQL-backed storage for matching preferences and discovery history."""

    def get_preferences(self, user_id: str) -> MatchPreferences:
        with SessionLocal() as session:
            return self._preferences(session.get(MatchPreferenceRecord, user_id))

    def update_preferences(self, user_id: str, values: MatchPreferences) -> MatchPreferences:
        with SessionLocal.begin() as session:
            record = session.get(MatchPreferenceRecord, user_id)
            if record is None:
                record = MatchPreferenceRecord(user_id=user_id)
                session.add(record)
            record.country_code = values.country_code
            record.gender = values.gender
            record.age_min = values.age_min
            record.age_max = values.age_max
            session.flush()
            return self._preferences(record)

    def candidate_ids(self, user_id: str) -> list[str]:
        with SessionLocal() as session:
            statement = (
                select(Profile.user_id)
                .join(User, User.id == Profile.user_id)
                .where(
                    Profile.user_id != user_id,
                    Profile.onboarding_completed.is_(True),
                    User.status.in_(("active", "seed")),
                    AvailabilityRepository.contactable_clause(),
                )
            )
            return list(session.scalars(statement))

    def exposures_for(self, viewer_id: str) -> dict[str, MatchExposure]:
        with SessionLocal() as session:
            records = session.scalars(
                select(MatchExposureRecord).where(MatchExposureRecord.viewer_id == viewer_id)
            )
            return {
                record.candidate_id: MatchExposure(record.last_shown_at, record.passed_at)
                for record in records
            }

    def record_shown(self, viewer_id: str, candidate_ids: list[str]) -> None:
        if not candidate_ids:
            return
        now = utc_now()
        with SessionLocal.begin() as session:
            records = {
                record.candidate_id: record
                for record in session.scalars(
                    select(MatchExposureRecord).where(
                        MatchExposureRecord.viewer_id == viewer_id,
                        MatchExposureRecord.candidate_id.in_(candidate_ids),
                    )
                )
            }
            for candidate_id in candidate_ids:
                record = records.get(candidate_id)
                if record is None:
                    session.add(
                        MatchExposureRecord(
                            viewer_id=viewer_id,
                            candidate_id=candidate_id,
                            last_shown_at=now,
                        )
                    )
                else:
                    record.last_shown_at = now

    def pass_candidate(self, viewer_id: str, candidate_id: str) -> bool:
        now = utc_now()
        with SessionLocal.begin() as session:
            eligible = session.scalar(
                select(Profile.user_id)
                .join(User, User.id == Profile.user_id)
                .where(
                    Profile.user_id == candidate_id,
                    Profile.user_id != viewer_id,
                    Profile.onboarding_completed.is_(True),
                    User.status.in_(("active", "seed")),
                    AvailabilityRepository.contactable_clause(),
                )
            )
            if eligible is None:
                return False

            record = session.get(
                MatchExposureRecord,
                {"viewer_id": viewer_id, "candidate_id": candidate_id},
            )
            if record is None:
                session.add(
                    MatchExposureRecord(
                        viewer_id=viewer_id,
                        candidate_id=candidate_id,
                        last_shown_at=now,
                        passed_at=now,
                    )
                )
            else:
                record.last_shown_at = now
                record.passed_at = now
            return True

    @staticmethod
    def _preferences(record: MatchPreferenceRecord | None) -> MatchPreferences:
        if record is None:
            return MatchPreferences()
        return MatchPreferences(
            country_code=record.country_code,
            gender=record.gender,
            age_min=record.age_min,
            age_max=record.age_max,
        )
