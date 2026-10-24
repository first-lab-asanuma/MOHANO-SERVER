from datetime import date
from typing import Optional
from uuid import uuid4

from app.core.errors import ServiceError
from app.schemas.profile import (
    ProfilePhoto,
    ProfilePhotoCreateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    PublicProfile,
)
from app.services.mock_store import MockStore


class ProfileService:
    """프로필 관련 비즈니스 로직. 현재는 MockStore만 사용한다."""

    def __init__(self, store: MockStore) -> None:
        self._store = store
        self._seed_candidates()

    def get_profile(self, user_id: str) -> ProfileResponse:
        with self._store.lock:
            return self._ensure_profile(user_id).model_copy(deep=True)

    def update_profile(self, user_id: str, payload: ProfileUpdateRequest) -> ProfileResponse:
        with self._store.lock:
            profile = self._ensure_profile(user_id)
            for field_name, value in payload.model_dump(exclude_unset=True).items():
                setattr(profile, field_name, value)
            profile.age = self._age_from(profile.birth_date)
            profile.onboarding_completed = self._is_onboarding_complete(profile)
            return profile.model_copy(deep=True)

    def add_photo(self, user_id: str, payload: ProfilePhotoCreateRequest) -> ProfileResponse:
        with self._store.lock:
            profile = self._ensure_profile(user_id)
            if len(profile.photos) >= 5:
                raise ServiceError("photo_limit_reached", "A profile can have up to five photos", 400)
            if payload.is_primary:
                for photo in profile.photos:
                    photo.is_primary = False
            is_primary = payload.is_primary or not profile.photos
            profile.photos.append(
                ProfilePhoto(
                    photo_id=str(uuid4()),
                    image_url=payload.image_ref,
                    position=len(profile.photos),
                    is_primary=is_primary,
                )
            )
            return profile.model_copy(deep=True)

    def remove_photo(self, user_id: str, photo_id: str) -> ProfileResponse:
        with self._store.lock:
            profile = self._ensure_profile(user_id)
            found = next((photo for photo in profile.photos if photo.photo_id == photo_id), None)
            if found is None:
                raise ServiceError("photo_not_found", "Photo not found", 404)
            was_primary = found.is_primary
            profile.photos.remove(found)
            for position, photo in enumerate(profile.photos):
                photo.position = position
            if was_primary and profile.photos:
                profile.photos[0].is_primary = True
            return profile.model_copy(deep=True)

    def get_public_profile(self, user_id: str) -> PublicProfile:
        with self._store.lock:
            profile = self._ensure_profile(user_id)
            primary_photo = next((photo for photo in profile.photos if photo.is_primary), None)
            return PublicProfile(
                nickname=profile.nickname,
                nationality=profile.nationality,
                gender=profile.gender,
                age=profile.age if profile.age_visible else None,
                age_visible=profile.age_visible,
                languages=list(profile.languages),
                mbti=profile.mbti,
                interest_codes=list(profile.interest_codes),
                introduction=profile.introduction,
                primary_photo=primary_photo.model_copy(deep=True) if primary_photo else None,
            )

    def _ensure_profile(self, user_id: str) -> ProfileResponse:
        profile = self._store.profiles.get(user_id)
        if profile is None:
            profile = ProfileResponse(user_id=user_id, nickname="New friend")
            self._store.profiles[user_id] = profile
        return profile

    @staticmethod
    def _age_from(birth_date: Optional[date]) -> Optional[int]:
        if birth_date is None:
            return None
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    @staticmethod
    def _is_onboarding_complete(profile: ProfileResponse) -> bool:
        return bool(profile.nationality and profile.gender and profile.birth_date)

    def _seed_candidates(self) -> None:
        candidates = [
            ProfileResponse(
                user_id="mock-hana",
                nickname="Hana",
                nationality="JP",
                gender="woman",
                birth_date=date(2000, 4, 12),
                age=self._age_from(date(2000, 4, 12)),
                languages=["ja", "en"],
                mbti="INFP",
                interest_codes=["bookstores", "photography", "deep_talks"],
                introduction="A quiet walk and a good question can make an ordinary day memorable.",
                photos=[ProfilePhoto(photo_id="photo-hana-1", image_url="mock://hana/primary", position=0, is_primary=True)],
                onboarding_completed=True,
            ),
            ProfileResponse(
                user_id="mock-yuki",
                nickname="Yuki-Mock",
                nationality="JP",
                gender="man",
                birth_date=date(1998, 9, 4),
                age=self._age_from(date(1998, 9, 4)),
                languages=["ja", "ko"],
                mbti="ISFJ",
                interest_codes=["coffee_walks", "indie_films", "languages"],
                introduction="Looking for someone to talk with slowly after a long day.",
                photos=[ProfilePhoto(photo_id="photo-yuki-1", image_url="mock://yuki/primary", position=0, is_primary=True)],
                onboarding_completed=True,
            ),
            ProfileResponse(
                user_id="mock-mina",
                nickname="Mina",
                nationality="KR",
                gender="woman",
                birth_date=date(1999, 1, 22),
                age=self._age_from(date(1999, 1, 22)),
                languages=["ko", "en"],
                mbti="ENFJ",
                interest_codes=["coffee_walks", "music", "travel"],
                introduction="Small everyday stories are my favorite conversation starters.",
                photos=[ProfilePhoto(photo_id="photo-mina-1", image_url="mock://mina/primary", position=0, is_primary=True)],
                onboarding_completed=True,
            ),
        ]
        with self._store.lock:
            for profile in candidates:
                self._store.profiles.setdefault(profile.user_id, profile)
                self._store.candidate_ids.add(profile.user_id)
