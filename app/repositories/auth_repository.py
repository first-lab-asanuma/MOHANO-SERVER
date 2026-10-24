from datetime import datetime
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.auth import AuthIdentity, RefreshSession
from app.models.profile import Profile
from app.models.user import User


@dataclass(frozen=True)
class IdentityLogin:
    user_id: str
    is_new_user: bool


class AuthRepository:
    """인증 사용자와 refresh session의 MySQL 저장소."""

    def create_anonymous_user(self) -> str:
        with SessionLocal.begin() as session:
            user = User(id=str(uuid4()), status="active")
            session.add(user)
            return user.id

    def get_or_create_identity(
        self,
        *,
        provider: str,
        provider_subject: str,
        provider_email: str | None,
    ) -> IdentityLogin:
        """검증된 외부 계정 식별자를 사용자와 안전하게 연결한다."""
        with SessionLocal.begin() as session:
            identity = session.scalar(
                select(AuthIdentity).where(
                    AuthIdentity.provider == provider,
                    AuthIdentity.provider_subject == provider_subject,
                )
            )
            if identity is not None:
                return IdentityLogin(user_id=identity.user_id, is_new_user=False)

            user_id = str(uuid4())
            session.add(User(id=user_id, status="active"))
            # 관계 객체를 사용하지 않는 명시적 ID 연결이므로 부모 users 행을 먼저
            # flush해 auth_identities의 외래 키 제약을 만족시킨다.
            session.flush()
            session.add(
                AuthIdentity(
                    user_id=user_id,
                    provider=provider,
                    provider_subject=provider_subject,
                    provider_email=provider_email,
                )
            )
            return IdentityLogin(user_id=user_id, is_new_user=True)

    def find_active_identity(self, *, provider: str, provider_subject: str) -> IdentityLogin | None:
        with SessionLocal() as session:
            identity = session.scalar(
                select(AuthIdentity).where(
                    AuthIdentity.provider == provider,
                    AuthIdentity.provider_subject == provider_subject,
                )
            )
            if identity is None:
                return None
            user = session.get(User, identity.user_id)
            if user is None or user.status != "active":
                return None
            return IdentityLogin(user_id=identity.user_id, is_new_user=False)

    def user_exists(self, user_id: str) -> bool:
        with SessionLocal() as session:
            return session.scalar(
                select(User.id).where(User.id == user_id, User.status == "active")
            ) is not None

    def onboarding_completed(self, user_id: str) -> bool:
        with SessionLocal() as session:
            return bool(
                session.scalar(
                    select(Profile.onboarding_completed).where(Profile.user_id == user_id)
                )
            )

    def create_refresh_session(self, user_id: str, jti_hash: str, expires_at: datetime) -> None:
        with SessionLocal.begin() as session:
            session.add(RefreshSession(user_id=user_id, refresh_jti_hash=jti_hash, expires_at=expires_at))

    def active_refresh_session(self, jti_hash: str) -> RefreshSession | None:
        with SessionLocal() as session:
            return session.scalar(
                select(RefreshSession).where(RefreshSession.refresh_jti_hash == jti_hash)
            )

    def revoke_refresh_session(self, jti_hash: str, revoked_at: datetime) -> None:
        with SessionLocal.begin() as session:
            record = session.scalar(
                select(RefreshSession).where(RefreshSession.refresh_jti_hash == jti_hash)
            )
            if record is not None:
                record.revoked_at = revoked_at
