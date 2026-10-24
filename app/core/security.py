import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Tuple
from uuid import uuid4

import jwt
from fastapi import HTTPException, status

from app.core.config import Settings, get_settings


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """MySQL DATETIME 값을 UTC aware datetime으로 정규화한다.

    MySQL은 timezone=True 선언에도 시간대 정보를 반환하지 않을 수 있다. 이 서비스는
    모든 저장 시각을 UTC로 기록하므로, naive 값은 UTC로 해석한다.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def hash_refresh_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode("utf-8")).hexdigest()


def create_access_token(subject: str, settings: Optional[Settings] = None) -> str:
    settings = settings or get_settings()
    expires_at = utc_now() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": subject, "typ": "access", "exp": expires_at},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(subject: str, settings: Optional[Settings] = None) -> Tuple[str, str, datetime]:
    settings = settings or get_settings()
    jti = str(uuid4())
    expires_at = utc_now() + timedelta(days=settings.refresh_token_expire_days)
    token = jwt.encode(
        {"sub": subject, "typ": "refresh", "jti": jti, "exp": expires_at},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, jti, expires_at


def decode_token(token: str, expected_type: str, settings: Optional[Settings] = None) -> dict[str, Any]:
    settings = settings or get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from error

    if payload.get("typ") != expected_type or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    return payload
