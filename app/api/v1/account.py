from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_current_user_id
from app.services.account_service import AccountService
from app.services.container import get_account_service

router = APIRouter(prefix="/me")


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    user_id: str = Depends(get_current_user_id),
    service: AccountService = Depends(get_account_service),
) -> Response:
    service.delete_account(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
