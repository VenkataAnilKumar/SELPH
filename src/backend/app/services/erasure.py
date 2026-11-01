"""
Right to erasure and right to portability.

erase_user: removes every row that belongs to a user, in foreign-key-safe order, inside one
transaction (all or nothing), then records a signed deletion certificate that proves the
erasure without retaining anything identifying. Audit logs are kept anonymized (spec: 2 years)
by reassigning them to a non-loginable tombstone account and stripping their details.

export_user_data: the same table walk, read-only, returning the user's data as JSON-safe dicts
with secrets (password hash, channel tokens, signing keys, push token) excluded.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import datetime, UTC
from typing import Any

from sqlalchemy import delete, select, update, or_
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Base, DeletionCertificate, TwinCertificate, User

TOMBSTONE_USER_ID = "deleted-user-tombstone"
TOMBSTONE_EMAIL = "deleted-account@selph.invalid"

# Never exported: credentials and key material.
SECRET_COLUMNS = {
    ("users", "password_hash"),
    ("users", "push_token"),
    ("channel_credentials", "credential_value"),
    ("twin_certificates", "private_key_ref"),
}
# Not user data (security bookkeeping / the certificates themselves).
NON_EXPORT_TABLES = {"revoked_tokens", "deletion_certificates"}
NON_ERASE_TABLES = {"deletion_certificates", "users", "audit_logs"}  # handled explicitly

PROVIDER_NOTE = (
    "Voice/avatar models held by third-party providers (ElevenLabs, HeyGen) are not deleted "
    "by SELPH: the provider integration has no deletion API. Request deletion with the provider directly."
)
EMAIL_NOTE = "No confirmation email is sent: SELPH has no outbound email service. This certificate is the confirmation."


# ── scoping: which rows belong to this user ──────────────────────────────────

def _twin_public_ids(db: Session, user_id: str) -> list[str]:
    return [r[0] for r in db.execute(select(TwinCertificate.twin_public_id).where(TwinCertificate.user_id == user_id))]


def _scope(db: Session, table, user_id: str):
    """SQL condition selecting the user's rows in `table`, or None if the table is unrelated."""
    cols = table.c
    name = table.name
    tables = Base.metadata.tables
    if name == "users":
        return cols.id == user_id
    if name == "referral_invites":
        return cols.referrer_user_id == user_id
    if name == "batch_sends":
        clusters = select(tables["message_clusters"].c.id).where(tables["message_clusters"].c.user_id == user_id)
        return cols.cluster_id.in_(clusters)
    if name == "verification_logs":
        certs = select(tables["twin_certificates"].c.id).where(tables["twin_certificates"].c.user_id == user_id)
        return cols.certificate_id.in_(certs)
    if name == "t2t_sessions":
        ids = _twin_public_ids(db, user_id)
        return or_(cols.initiating_twin.in_(ids), cols.receiving_twin.in_(ids)) if ids else None
    if "user_id" in cols:
        return cols.user_id == user_id
    return None


def _user_tables():
    # sorted_tables is parents-first; children must be deleted first, so reverse it.
    return list(reversed(Base.metadata.sorted_tables))


# ── erasure ──────────────────────────────────────────────────────────────────

def _signing_key() -> bytes:
    settings = get_settings()
    base = settings.certificate_signing_key or settings.jwt_secret_key
    return hmac.new(base.encode("utf-8"), b"selph-deletion-certificate-v1", hashlib.sha256).digest()


def _canonical(cert_id: str, subject_hash: str, completed_at: datetime, summary: dict) -> bytes:
    return "|".join(
        [cert_id, subject_hash, completed_at.replace(microsecond=0).isoformat(), json.dumps(summary, sort_keys=True)]
    ).encode("utf-8")


def _sign(cert_id: str, subject_hash: str, completed_at: datetime, summary: dict) -> str:
    return hmac.new(_signing_key(), _canonical(cert_id, subject_hash, completed_at, summary), hashlib.sha256).hexdigest()


def subject_hash_for(user_id: str, cert_id: str) -> str:
    return hashlib.sha256(f"selph-erasure:{user_id}:{cert_id}".encode("utf-8")).hexdigest()


def verify_certificate(cert: DeletionCertificate) -> bool:
    expected = _sign(cert.id, cert.subject_hash, cert.completed_at, cert.summary)
    return hmac.compare_digest(expected.encode("ascii"), (cert.signature or "").encode("ascii", "ignore"))


def _ensure_tombstone(db: Session) -> None:
    if db.get(User, TOMBSTONE_USER_ID) is None:
        db.add(User(
            id=TOMBSTONE_USER_ID,
            email=TOMBSTONE_EMAIL,
            password_hash="!",  # not a valid hash: nothing can ever verify against it
            name="Deleted account",
            is_active=False,
        ))
        db.flush()


def erase_user(db: Session, user_id: str) -> DeletionCertificate:
    """Erase everything belonging to `user_id` atomically and return the signed certificate."""
    if user_id == TOMBSTONE_USER_ID:
        raise ValueError("The tombstone account cannot be erased")
    if db.get(User, user_id) is None:
        raise ValueError("User not found")

    counts: dict[str, int] = {}
    try:
        _ensure_tombstone(db)
        tables = Base.metadata.tables

        # 1. Keep audit logs, anonymized.
        audit = tables["audit_logs"]
        result = db.execute(
            update(audit)
            .where(audit.c.user_id == user_id)
            .values(user_id=TOMBSTONE_USER_ID, resource_id=None, details={}, ip_address=None, user_agent=None)
        )
        counts["audit_logs (anonymized, retained)"] = result.rowcount or 0

        # 2. Other people's referral rows that merely point at this user: detach, keep theirs.
        invites = tables["referral_invites"]
        db.execute(update(invites).where(invites.c.invitee_user_id == user_id).values(invitee_user_id=None))

        # 3. Delete the user's rows, children before parents. Scopes are computed first because
        #    deleting a parent (e.g. certificates) would otherwise erase the way to find children.
        plan = []
        for table in _user_tables():
            if table.name in NON_ERASE_TABLES:
                continue
            cond = _scope(db, table, user_id)
            if cond is not None:
                plan.append((table, cond))
        for table, cond in plan:
            deleted = db.execute(delete(table).where(cond)).rowcount or 0
            if deleted:
                counts[table.name] = deleted

        db.execute(delete(tables["users"]).where(tables["users"].c.id == user_id))
        counts["users"] = 1

        # 4. Certificate.
        now = datetime.now(UTC).replace(tzinfo=None)
        cert_id = str(uuid.uuid4())
        summary = {"tables": counts, "notes": [PROVIDER_NOTE, EMAIL_NOTE]}
        subject_hash = subject_hash_for(user_id, cert_id)
        cert = DeletionCertificate(
            id=cert_id,
            subject_hash=subject_hash,
            completed_at=now,
            summary=summary,
            signature=_sign(cert_id, subject_hash, now, summary),
        )
        db.add(cert)
        db.commit()
        db.refresh(cert)
        return cert
    except Exception:
        db.rollback()
        raise


# ── portability ──────────────────────────────────────────────────────────────

def _jsonable(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
        return value
    return str(value)


def export_user_data(db: Session, user_id: str) -> dict:
    """Everything SELPH stores about the user as JSON-safe dicts, minus secrets."""
    data: dict[str, list[dict]] = {}
    for table in reversed(_user_tables()):  # parents first reads naturally
        if table.name in NON_EXPORT_TABLES:
            continue
        cond = _scope(db, table, user_id)
        if cond is None:
            continue
        rows = db.execute(select(table).where(cond)).mappings().all()
        if not rows:
            continue
        data[table.name] = [
            {k: _jsonable(v) for k, v in row.items() if (table.name, k) not in SECRET_COLUMNS}
            for row in rows
        ]
    return {
        "exported_at": datetime.now(UTC).isoformat(),
        "format": "selph-export-v1",
        "excluded": sorted(f"{t}.{c}" for t, c in SECRET_COLUMNS),
        "data": data,
    }
