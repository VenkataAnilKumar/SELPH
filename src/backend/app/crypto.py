"""
Encryption at rest for stored secrets (channel OAuth tokens).

Values are stored as ``enc:v1:<fernet-token>``. Reads transparently accept legacy
plaintext rows (no prefix), so existing databases keep working and can be upgraded with
``scripts/encrypt_credentials.py``.

Keys come from ``CREDENTIAL_ENCRYPTION_KEY``: one or more comma-separated Fernet keys
(``python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"``).
The first key encrypts; every key can decrypt, which allows zero-downtime rotation.

In production an explicit key is required and encryption fails closed without one.
In development a key is derived from JWT_SECRET_KEY so local setups work unconfigured.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from app.config import get_settings

PREFIX = "enc:v1:"


class EncryptionConfigError(RuntimeError):
    """Raised when secrets cannot be encrypted safely (e.g. production without a key)."""


def _keys() -> list[bytes]:
    settings = get_settings()
    raw = [k.strip() for k in (settings.credential_encryption_key or "").split(",") if k.strip()]
    if raw:
        return [k.encode() for k in raw]
    if settings.environment.lower() == "production":
        raise EncryptionConfigError(
            "CREDENTIAL_ENCRYPTION_KEY is required in production to store channel credentials"
        )
    digest = hashlib.sha256(("selph-dev-credential-key:" + settings.jwt_secret_key).encode()).digest()
    return [base64.urlsafe_b64encode(digest)]


def _fernet() -> MultiFernet:
    return MultiFernet([Fernet(k) for k in _keys()])


def is_encrypted(value: str | None) -> bool:
    return bool(value) and value.startswith(PREFIX)


def _encrypt_plain(plaintext: str) -> str:
    return PREFIX + _fernet().encrypt(plaintext.encode("utf-8")).decode("ascii")


def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret. Already-encrypted input is returned unchanged (idempotent)."""
    if plaintext is None or is_encrypted(plaintext):
        return plaintext
    return _encrypt_plain(plaintext)


def reencrypt_secret(value: str) -> str:
    """Decrypt (or accept plaintext) and encrypt again under the current primary key."""
    if value is None:
        return value
    return _encrypt_plain(decrypt_secret(value))


def decrypt_secret(value: str) -> str:
    """Decrypt a stored secret; legacy plaintext (no prefix) is returned as-is."""
    if value is None or not is_encrypted(value):
        return value
    try:
        return _fernet().decrypt(value[len(PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise EncryptionConfigError(
            "Stored credential cannot be decrypted with the configured CREDENTIAL_ENCRYPTION_KEY"
        ) from exc
