from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfilePhotoCreateRequest, ProfilePhotoUploadRequest, ProfilePhotoUploadUrl, ProfileResponse, ProfileUpdateRequest, PublicProfile
from app.services.object_storage_service import ObjectStorageService


class DatabaseProfileService:
    """프로필 비즈니스 계약을 MySQL repository로 연결한다."""

    def __init__(
        self,
        repository: ProfileRepository,
        storage: ObjectStorageService,
        *,
        seed_candidates: bool = False,
    ) -> None:
        self._repository = repository
        self._storage = storage
        if seed_candidates:
            self._repository.seed_candidates()

    def get_profile(self, user_id: str) -> ProfileResponse:
        return self._with_photo_urls(self._repository.get(user_id))

    def update_profile(self, user_id: str, payload: ProfileUpdateRequest) -> ProfileResponse:
        return self._with_photo_urls(self._repository.update(user_id, payload))

    def add_photo(self, user_id: str, payload: ProfilePhotoCreateRequest) -> ProfileResponse:
        return self._with_photo_urls(self._repository.add_photo(user_id, payload))

    def create_photo_upload(self, user_id: str, payload: ProfilePhotoUploadRequest) -> ProfilePhotoUploadUrl:
        return self._storage.create_upload_url(user_id, payload)

    def complete_photo_upload(self, user_id: str, upload_id: str) -> ProfileResponse:
        upload_id = self._storage.normalize_upload_id(upload_id)
        staging_key = self._storage.staging_key(user_id, upload_id)
        try:
            self._repository.ensure_photo_capacity(user_id)
        except Exception:
            try:
                self._storage.delete(staging_key)
            except Exception:
                pass
            raise
        staging_key, content_type = self._storage.validate_staged_upload(user_id, upload_id)
        final_key = self._storage.profile_key(user_id, upload_id)
        self._storage.promote(staging_key, final_key, content_type)
        try:
            profile = self._repository.add_photo_from_storage(user_id, upload_id, final_key)
        except Exception:
            try:
                self._storage.delete(final_key)
            except Exception:
                pass
            raise
        return self._with_photo_urls(profile)

    def remove_photo(self, user_id: str, photo_id: str) -> ProfileResponse:
        storage_key = self._repository.photo_storage_key(user_id, photo_id)
        self._storage.delete(storage_key)
        return self._with_photo_urls(self._repository.remove_photo(user_id, photo_id))

    def get_public_profile(self, user_id: str) -> PublicProfile:
        return self._with_photo_urls(self._repository.public(user_id))

    def _with_photo_urls(self, profile: ProfileResponse | PublicProfile) -> ProfileResponse | PublicProfile:
        if isinstance(profile, PublicProfile) and not isinstance(profile, ProfileResponse):
            primary = profile.primary_photo
            if primary is None:
                return profile
            return profile.model_copy(
                update={'primary_photo': primary.model_copy(update={'image_url': self._storage.download_url(primary.image_url)})},
            )

        photos = [photo.model_copy(update={'image_url': self._storage.download_url(photo.image_url)}) for photo in profile.photos]
        primary = next((photo for photo in photos if photo.is_primary), None)
        return profile.model_copy(update={'photos': photos, 'primary_photo': primary})
