"""Encryption at rest for channel credentials, and fail-closed webhooks."""

import base64
import hashlib
import hmac as hmac_lib
import json

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import text

from app.channels.instagram import InstagramAdapter
from app.config import get_settings
from app import crypto
from app.crypto import EncryptionConfigError, decrypt_secret, encrypt_secret, is_encrypted
from app.models import ChannelCredential
from app.services.channel import ChannelService


# ── encryption at rest ───────────────────────────────────────────────────────

def test_roundtrip_and_ciphertext_is_not_plaintext():
    secret = "EAAG-super-secret-page-token"
    enc = encrypt_secret(secret)
    assert enc.startswith("enc:v1:") and secret not in enc
    assert decrypt_secret(enc) == secret
    assert encrypt_secret(enc) == enc  # idempotent: never double-encrypts


def test_legacy_plaintext_is_still_readable():
    assert decrypt_secret("plain-legacy-token") == "plain-legacy-token"
    assert not is_encrypted("plain-legacy-token")


def test_database_row_holds_ciphertext_but_orm_returns_plaintext(test_db, test_user):
    ChannelService.upsert_credential(
        test_db, test_user.id, "gmail",
        json.dumps({"access_token": "AT-123", "refresh_token": "RT-456"}),
        scope='{"email": "u@gmail.com"}',
    )
    raw = test_db.execute(text("SELECT credential_value FROM channel_credentials")).scalar()
    assert raw.startswith("enc:v1:")
    assert "AT-123" not in raw and "RT-456" not in raw

    cred = test_db.query(ChannelCredential).first()
    assert json.loads(cred.credential_value)["access_token"] == "AT-123"


def test_legacy_plaintext_row_is_read_and_upgraded_on_next_write(test_db, test_user):
    test_db.execute(
        text(
            "INSERT INTO channel_credentials (id, created_at, updated_at, user_id, channel, "
            "credential_type, credential_value, is_active) "
            "VALUES ('legacy-1', datetime('now'), datetime('now'), :u, 'instagram_dm', 'oauth_token', 'LEGACY-TOKEN', 1)"
        ),
        {"u": test_user.id},
    )
    test_db.commit()
    cred = ChannelService.get_credential(test_db, test_user.id, "instagram_dm")
    assert cred.credential_value == "LEGACY-TOKEN"

    ChannelService.upsert_credential(test_db, test_user.id, "instagram_dm", "NEW-TOKEN")
    raw = test_db.execute(text("SELECT credential_value FROM channel_credentials")).scalar()
    assert raw.startswith("enc:v1:")


def test_key_rotation_new_key_encrypts_old_key_still_decrypts(monkeypatch):
    old, new = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    settings = get_settings()
    monkeypatch.setattr(settings, "credential_encryption_key", old)
    token = encrypt_secret("rotate-me")

    monkeypatch.setattr(settings, "credential_encryption_key", f"{new},{old}")
    assert decrypt_secret(token) == "rotate-me"            # old ciphertext still readable
    assert decrypt_secret(encrypt_secret("fresh")) == "fresh"

    monkeypatch.setattr(settings, "credential_encryption_key", new)  # old key retired
    with pytest.raises(EncryptionConfigError):
        decrypt_secret(token)


def test_production_requires_explicit_key(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "credential_encryption_key", "")
    with pytest.raises(EncryptionConfigError):
        encrypt_secret("anything")


def test_readiness_reports_missing_key_in_production(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "credential_encryption_key", "")
    checks = client.get("/ready").json()["checks"]
    assert checks["credential_encryption"]["ok"] is False


# ── webhooks fail closed ─────────────────────────────────────────────────────

def _pubsub_body():
    data = base64.urlsafe_b64encode(json.dumps({"emailAddress": "x@gmail.com", "historyId": "1"}).encode()).decode()
    return {"message": {"data": data, "messageId": "m1"}, "subscription": "s"}


def _ig_body():
    return {"object": "instagram", "entry": []}


def test_instagram_webhook_rejected_when_secret_unset(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "meta_app_secret", "")
    r = client.post("/v1/channels/instagram/webhook", json=_ig_body())
    assert r.status_code == 503


def test_gmail_webhook_rejected_when_secret_unset(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "google_webhook_secret", "")
    r = client.post("/v1/channels/gmail/webhook", json=_pubsub_body())
    assert r.status_code == 503


def test_unsigned_webhooks_allowed_only_in_development_with_opt_in(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "google_webhook_secret", "")
    monkeypatch.setattr(settings, "allow_unsigned_webhooks", True)

    monkeypatch.setattr(settings, "environment", "development")
    assert client.post("/v1/channels/gmail/webhook", json=_pubsub_body()).status_code == 200

    monkeypatch.setattr(settings, "environment", "production")
    assert client.post("/v1/channels/gmail/webhook", json=_pubsub_body()).status_code == 503


def test_gmail_secret_accepted_via_query_param_for_pubsub_push(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "google_webhook_secret", "s3cret")
    assert client.post("/v1/channels/gmail/webhook?token=wrong", json=_pubsub_body()).status_code == 403
    assert client.post("/v1/channels/gmail/webhook?token=s3cret", json=_pubsub_body()).status_code == 200
    assert client.post("/v1/channels/gmail/webhook", json=_pubsub_body()).status_code == 403


def test_gmail_non_ascii_token_is_rejected_not_a_500(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "google_webhook_secret", "s3cret")
    r = client.post("/v1/channels/gmail/webhook?token=%C3%A9%E2%82%AC", json=_pubsub_body())
    assert r.status_code == 403


def test_instagram_signature_validation(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "meta_app_secret", "app-secret")
    body = json.dumps(_ig_body()).encode()
    good = "sha256=" + hmac_lib.new(b"app-secret", body, hashlib.sha256).hexdigest()

    headers = {"Content-Type": "application/json"}
    assert client.post("/v1/channels/instagram/webhook", content=body, headers={**headers, "X-Hub-Signature-256": good}).status_code == 200
    assert client.post("/v1/channels/instagram/webhook", content=body, headers={**headers, "X-Hub-Signature-256": "sha256=deadbeef"}).status_code == 403
    assert client.post("/v1/channels/instagram/webhook", content=body, headers=headers).status_code == 403
    # unicode in the signature header must not crash the comparison
    assert client.post("/v1/channels/instagram/webhook", content=body, headers={**headers, "X-Hub-Signature-256": "sha256=\u00e9".encode("latin-1")}).status_code == 403


def test_empty_app_secret_never_validates_a_signature(monkeypatch):
    monkeypatch.setattr(get_settings(), "meta_app_secret", "")
    body = b"{}"
    forged = "sha256=" + hmac_lib.new(b"", body, hashlib.sha256).hexdigest()
    assert InstagramAdapter().verify_signature(body, forged) is False


def test_reencrypt_moves_ciphertext_to_new_primary_key(monkeypatch):
    from app.crypto import reencrypt_secret

    old, new = Fernet.generate_key().decode(), Fernet.generate_key().decode()
    settings = get_settings()
    monkeypatch.setattr(settings, "credential_encryption_key", old)
    token = encrypt_secret("move-me")

    monkeypatch.setattr(settings, "credential_encryption_key", f"{new},{old}")
    moved = reencrypt_secret(token)
    assert moved != token

    monkeypatch.setattr(settings, "credential_encryption_key", new)  # old key dropped
    assert decrypt_secret(moved) == "move-me"
    assert reencrypt_secret("legacy-plain") != "legacy-plain"


# ── approval is mandatory (defense in depth below the HTTP layer) ────────────

@pytest.mark.parametrize("status", ["pending_approval", "rejected", "sent"])
def test_service_refuses_to_send_unapproved_drafts(test_db, test_user, status):
    from unittest.mock import patch
    from app.models import Draft, Message, Twin

    twin = test_db.query(Twin).filter(Twin.user_id == test_user.id).first()
    msg = Message(user_id=test_user.id, channel="gmail", sender_id="a@b.com", sender_name="A", content="hi")
    test_db.add(msg); test_db.commit()
    draft = Draft(message_id=msg.id, user_id=test_user.id, twin_id=twin.id, content="reply", status=status)
    test_db.add(draft); test_db.commit()
    ChannelService.upsert_credential(test_db, test_user.id, "gmail", json.dumps({"access_token": "x"}))

    with patch("app.services.channel.get_adapter") as get_adapter:
        assert ChannelService.send_draft_reply(test_db, draft.id) is False
        get_adapter.assert_not_called()  # nothing left the building


def test_service_sends_approved_draft(test_db, test_user):
    from unittest.mock import MagicMock, patch
    from app.models import Draft, Message, Twin

    twin = test_db.query(Twin).filter(Twin.user_id == test_user.id).first()
    msg = Message(user_id=test_user.id, channel="gmail", sender_id="a@b.com", sender_name="A", content="hi")
    test_db.add(msg); test_db.commit()
    draft = Draft(message_id=msg.id, user_id=test_user.id, twin_id=twin.id, content="reply", status="approved")
    test_db.add(draft); test_db.commit()
    ChannelService.upsert_credential(test_db, test_user.id, "gmail", json.dumps({"access_token": "x"}))

    adapter = MagicMock()
    adapter.send_reply.return_value = True
    with patch("app.services.channel.get_adapter", return_value=adapter):
        assert ChannelService.send_draft_reply(test_db, draft.id) is True
    adapter.send_reply.assert_called_once()


# ── twin signing secrets are encrypted at rest too ───────────────────────────

def test_twin_signing_secret_is_encrypted_in_the_database(test_db, test_user):
    from app.services.verification import VerificationService

    cert = VerificationService.issue_certificate(test_db, test_user.id)
    plain = cert.private_key_ref
    raw = test_db.execute(text("SELECT private_key_ref FROM twin_certificates")).scalar()

    assert raw.startswith("enc:v1:") and plain not in raw and len(raw) <= 200
    sig = VerificationService.sign_message(plain, "hash")          # signing still works with the decrypted value
    assert sig and VerificationService.sign_message(cert.private_key_ref, "hash") == sig


def test_legacy_plaintext_twin_secret_still_signs(test_db, test_user):
    from app.services.verification import VerificationService

    cert = VerificationService.issue_certificate(test_db, test_user.id)
    secret = cert.private_key_ref
    test_db.execute(text("UPDATE twin_certificates SET private_key_ref = :s"), {"s": secret})  # as stored before this change
    test_db.commit(); test_db.expire_all()
    assert VerificationService.issue_certificate(test_db, test_user.id).private_key_ref == secret
