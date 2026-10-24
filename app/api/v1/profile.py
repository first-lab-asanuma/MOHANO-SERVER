from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.schemas.profile import ProfilePhotoUploadRequest, ProfilePhotoUploadUrl, ProfileResponse, ProfileUpdateRequest
from app.services.container import get_profile_service
from app.services.database_profile_service import DatabaseProfileService

router = APIRouter(prefix="/me/profile")


@router.get("", response_model=ProfileResponse)
def get_profile(
    user_id: str = Depends(get_current_user_id),
    service: DatabaseProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    return service.get_profile(user_id)


@router.patch("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    service: DatabaseProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    return service.update_profile(user_id, payload)


@router.post("/photos/upload-requests", response_model=ProfilePhotoUploadUrl)
def create_profile_photo_upload(
    payload: ProfilePhotoUploadRequest,
    user_id: str = Depends(get_current_user_id),
    service: DatabaseProfileService = Depends(get_profile_service),
) -> ProfilePhotoUploadUrl:
    return service.create_photo_upload(user_id, payload)


@router.post("/photos/upload-requests/{upload_id}/complete", response_model=ProfileResponse)
def complete_profile_photo_upload(
    upload_id: str,
    user_id: str = Depends(get_current_user_id),
    service: DatabaseProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    return service.complete_photo_upload(user_id, upload_id)


@router.delete("/photos/{photo_id}", response_model=ProfileResponse)
def remove_profile_photo(
    photo_id: str,
    user_id: str = Depends(get_current_user_id),
    service: DatabaseProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    return service.remove_photo(user_id, photo_id)
