"""
Token revocation service (database-backed so it works without Redis)
"""

from datetime import datetime, UTC
from typing import Optional

from sqlalchemy.orm import Session

from app.models import RevokedToken
from app.security import token_revocation_key


def _expiry(payload: dict) -> datetime:
    exp = payload.get("exp")
    if exp is None:
        return datetime.now(UTC).replace(tzinfo=None)
    return datetime.fromtimestamp(int(exp), UTC).replace(tzinfo=None)


class TokenRevocationService:
    @staticmethod
    def purge_expired(db: Session) -> int:
        """Delete revocation rows for tokens that have expired anyway."""
        now = datetime.now(UTC).replace(tzinfo=None)
        deleted = db.query(RevokedToken).filter(RevokedToken.expires_at < now).delete()
        db.commit()
        return deleted

    @staticmethod
    def revoke(db: Session, token: str, payload: dict, user_id: str) -> RevokedToken:
        """Revoke a token (idempotent)."""
        key = token_revocation_key(token, payload)
        existing = db.query(RevokedToken).filter(RevokedToken.token_key == key).first()
        if existing:
            return existing
        row = RevokedToken(
            token_key=key,
            user_id=user_id,
            token_type=payload.get("type", "access"),
            expires_at=_expiry(payload),
        )
        db.add(row)
        db.commit()
        return row

    @staticmethod
    def is_revoked(db: Session, token: str, payload: Optional[dict] = None) -> bool:
        key = token_revocation_key(token, payload)
        return db.query(RevokedToken.id).filter(RevokedToken.token_key == key).first() is not None
