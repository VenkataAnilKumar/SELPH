"""Twin verification service for signing and validation."""

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, UTC, timedelta

from sqlalchemy.orm import Session
from app.models import TwinCertificate, VerificationLog


class VerificationService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def _build_twin_public_id() -> str:
        return f"twn_{secrets.token_hex(6)}"

    @staticmethod
    def _signature(secret: str, message_hash: str) -> str:
        digest = hmac.new(secret.encode("utf-8"), message_hash.encode("utf-8"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8")

    @staticmethod
    def issue_certificate(db: Session, user_id: str) -> TwinCertificate:
        existing = db.query(TwinCertificate).filter(TwinCertificate.user_id == user_id, TwinCertificate.revoked_at.is_(None)).first()
        if existing:
            return existing

        secret = secrets.token_urlsafe(32)
        now = VerificationService._now()
        cert = TwinCertificate(
            user_id=user_id,
            twin_public_id=VerificationService._build_twin_public_id(),
            public_key=f"hmac-sha256:{hashlib.sha256(secret.encode('utf-8')).hexdigest()}",
            private_key_ref=secret,
            issued_at=now,
            expires_at=now + timedelta(days=365),
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)
        return cert

    @staticmethod
    def get_certificate(db: Session, user_id: str) -> TwinCertificate | None:
        return db.query(TwinCertificate).filter(TwinCertificate.user_id == user_id).order_by(TwinCertificate.created_at.desc()).first()

    @staticmethod
    def get_certificate_by_twin_id(db: Session, twin_id: str) -> TwinCertificate | None:
        return db.query(TwinCertificate).filter(TwinCertificate.twin_public_id == twin_id).first()

    @staticmethod
    def sign_message(private_key_ref: str, message_hash: str) -> str:
        return VerificationService._signature(private_key_ref, message_hash)

    @staticmethod
    def verify_message(db: Session, twin_public_id: str, message_hash: str, signature: str | None) -> dict:
        cert = VerificationService.get_certificate_by_twin_id(db, twin_public_id)
        now = VerificationService._now()
        valid = False
        reason = None

        if not cert:
            reason = "certificate_not_found"
        elif cert.revoked_at:
            reason = "certificate_revoked"
        elif cert.expires_at <= now:
            reason = "certificate_expired"
        elif not signature:
            reason = "missing_signature"
        else:
            expected = VerificationService._signature(cert.private_key_ref, message_hash)
            valid = hmac.compare_digest(expected, signature)
            if not valid:
                reason = "signature_mismatch"

        log = VerificationLog(
            certificate_id=cert.id if cert else None,
            twin_public_id=twin_public_id,
            message_hash=message_hash,
            valid=valid,
            reason=reason,
            verified_at=now,
        )
        db.add(log)
        db.commit()

        return {"valid": valid, "reason": reason}

    @staticmethod
    def revoke_certificate(db: Session, user_id: str, reason: str | None = None) -> TwinCertificate | None:
        cert = VerificationService.get_certificate(db, user_id)
        if not cert:
            return None
        cert.revoked_at = VerificationService._now()
        cert.revoke_reason = reason
        db.add(cert)
        db.commit()
        db.refresh(cert)
        return cert
