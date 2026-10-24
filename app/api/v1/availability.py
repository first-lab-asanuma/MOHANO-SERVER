from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.schemas.availability import AvailabilityResponse, AvailabilityUpdateRequest
from app.services.container import get_availability_repository
from app.repositories.availability_repository import AvailabilityRepository


router = APIRouter(prefix="/me/availability")


@router.get("", response_model=AvailabilityResponse)
def get_availability(
    user_id: str = Depends(get_current_user_id),
    repository: AvailabilityRepository = Depends(get_availability_repository),
) -> AvailabilityResponse:
    return repository.get(user_id)


@router.post("/heartbeat", response_model=AvailabilityResponse)
def heartbeat(
    user_id: str = Depends(get_current_user_id),
    repository: AvailabilityRepository = Depends(get_availability_repository),
) -> AvailabilityResponse:
    return repository.heartbeat(user_id)


@router.put("", response_model=AvailabilityResponse)
def update_availability(
    payload: AvailabilityUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    repository: AvailabilityRepository = Depends(get_availability_repository),
) -> AvailabilityResponse:
    return repository.update(user_id, payload)
