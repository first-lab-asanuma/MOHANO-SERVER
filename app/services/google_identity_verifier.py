"""Google ID token 검증을 인증 service에서 분리한다."""

from dataclasses import dataclass

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from app.core.config import Settings, get_settings
from app.core.errors import ServiceError


@dataclass(frozen=True)
class VerifiedGoogleIdentity:
    subject: str
    email: str | None


class GoogleIdentityVerifier:
    """Google 공개 키와 등록된 Web client ID로 ID token을 검증한다."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def verify(self, credential: str) -> VerifiedGoogleIdentity:
        audience = self._settings.google_web_client_id.strip()
        if not audience or audience.startswith("replace-with-"):
            raise ServiceError(
                "google_sign_in_not_configured",
                "Google sign-in is not configured on this server.",
                503,
            )

        try:
            claims = id_token.verify_oauth2_token(credential, Request(), audience)
        except (GoogleAuthError, ValueError) as error:
            raise ServiceError("invalid_google_id_token", "Google sign-in could not be verified.", 401) from error

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise ServiceError("invalid_google_id_token", "Google sign-in could not be verified.", 401)

        email = claims.get("email")
        return VerifiedGoogleIdentity(
            subject=subject,
            email=email if isinstance(email, str) else None,
        )
