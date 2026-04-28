"""
Security utilities for password hashing and JWT tokens
"""

from datetime import datetime, timedelta, UTC
from typing import Optional
import logging
import jwt
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Return UTC now without deprecated utcnow()."""
    return datetime.now(UTC)


def _build_pwd_context() -> CryptContext:
    """Build a password context with a safe runtime fallback.

    Some Python/passlib/bcrypt combinations (notably bcrypt>=4.1 with older
    passlib) can raise runtime errors during backend capability checks.
    """
    bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    try:
        probe = "security-probe-password"
        probe_hash = bcrypt_context.hash(probe)
        if not bcrypt_context.verify(probe, probe_hash):
            raise RuntimeError("bcrypt self-test failed")
        return bcrypt_context
    except Exception as exc:
        logger.warning(
            "bcrypt unavailable or incompatible; falling back to pbkdf2_sha256: %s",
            exc,
        )
        return CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# Password hashing context
pwd_context = _build_pwd_context()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, int]:
    """
    Create a JWT access token
    Returns: (token, expires_in_seconds)
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = _utcnow() + expires_delta
    else:
        expire = _utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    expires_in = int(expires_delta.total_seconds()) if expires_delta else 86400
    return encoded_jwt, expires_in


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()

    if expires_delta:
        expire = _utcnow() + expires_delta
    else:
        expire = _utcnow() + timedelta(days=7)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token
    Returns: payload dict or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
