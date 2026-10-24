from fastapi import APIRouter, Depends, Response, status

from app.schemas.auth import GoogleExchangeRequest, RefreshTokenRequest, TokenPair
from app.services.auth_service import AuthService
from app.services.container import get_auth_service

router = APIRouter()


@router.post("/anonymous", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def create_anonymous_session(
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return service.create_anonymous_session()


@router.post("/google/exchange", response_model=TokenPair)
def exchange_google_id_token(
    payload: GoogleExchangeRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return service.sign_in_with_google(payload)


@router.post("/refresh", response_model=TokenPair)
def refresh_session(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenPair:
    return service.refresh_session(payload)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    service.logout(payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
