from typing import Optional
from app.core.errors import ServiceError
from app.core.security import (
    as_utc,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_refresh_jti,
    utc_now,
)
from app.schemas.auth import GoogleExchangeRequest, RefreshTokenRequest, TokenPair
from app.repositories.auth_repository import AuthRepository
from app.services.google_identity_verifier import GoogleIdentityVerifier


class AuthService:
    """JWT 발급·회전 규칙을 담당하는 인증 service."""

    def __init__(self, repository: AuthRepository, google_identity_verifier: GoogleIdentityVerifier) -> None:
        self._repository = repository
        self._google_identity_verifier = google_identity_verifier

    def create_anonymous_session(self) -> TokenPair:
        return self._issue_token_pair(self._repository.create_anonymous_user(), is_new_user=True)

    def sign_in_with_google(self, payload: GoogleExchangeRequest) -> TokenPair:
        identity = self._google_identity_verifier.verify(payload.id_token)
        if payload.create_account:
            login = self._repository.get_or_create_identity(
                provider="google",
                provider_subject=identity.subject,
                provider_email=identity.email,
            )
        else:
            login = self._repository.find_active_identity(
                provider="google",
                provider_subject=identity.subject,
            )
            if login is None:
                raise ServiceError(
                    "account_not_found",
                    "No MOHANO account is linked to this Google account.",
                    404,
                )
        return self._issue_token_pair(login.user_id, is_new_user=login.is_new_user)

    def refresh_session(self, payload: RefreshTokenRequest) -> TokenPair:
        token = decode_token(payload.refresh_token, expected_type="refresh")
        refresh_jti = token.get("jti")
        if not refresh_jti:
            raise ServiceError("invalid_refresh_token", "Invalid refresh token", 401)

        session_key = hash_refresh_jti(str(refresh_jti))
        session = self._repository.active_refresh_session(session_key)
        if session is None or session.revoked_at is not None or as_utc(session.expires_at) <= utc_now():
            raise ServiceError("refresh_session_expired", "Refresh session expired", 401)
        if not self._repository.user_exists(str(token["sub"])):
            raise ServiceError("user_unavailable", "User unavailable", 401)
        self._repository.revoke_refresh_session(session_key, utc_now())
        return self._issue_token_pair(str(token["sub"]))

    def logout(self, payload: RefreshTokenRequest) -> None:
        token = decode_token(payload.refresh_token, expected_type="refresh")
        refresh_jti = token.get("jti")
        if not refresh_jti:
            return
        self._repository.revoke_refresh_session(hash_refresh_jti(str(refresh_jti)), utc_now())

    def _issue_token_pair(self, user_id: str, *, is_new_user: bool = False) -> TokenPair:
        refresh_token, refresh_jti, refresh_expires_at = create_refresh_token(user_id)
        self._repository.create_refresh_session(
            user_id,
            hash_refresh_jti(refresh_jti),
            refresh_expires_at,
        )
        return TokenPair(
            access_token=create_access_token(user_id),
            refresh_token=refresh_token,
            is_new_user=is_new_user,
            needs_onboarding=not self._repository.onboarding_completed(user_id),
        )
