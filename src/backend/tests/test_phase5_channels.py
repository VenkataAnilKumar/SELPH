"""
Phase 5 tests — Channel adapters, OAuth flows, webhook ingestion, and reply delivery.

Test coverage:
  - InstagramAdapter: build_authorization_url, verify_webhook, parse_webhook_event,
    verify_signature, exchange_code_for_token (mocked), send_reply (mocked)
  - GmailAdapter: build_authorization_url, parse_pubsub_notification, _extract_plain_text_body,
    exchange_code_for_token (mocked), send_reply (mocked), fetch_new_messages (mocked)
  - ChannelRegistry: get_adapter, list_channels, unknown channel raises
  - ChannelService: upsert_credential, get_credential, find_user_by_instagram_page,
    find_user_by_gmail_address, send_draft_reply (mocked adapter)
  - API router: GET /instagram/webhook, POST /instagram/webhook, GET /instagram/oauth,
    GET /gmail/oauth, POST /gmail/webhook, POST /send-reply, legacy connect endpoints
"""

import base64
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import User, ChannelCredential, Draft, Message
from app.models.twin import Twin
from app.models.base import utcnow
from app.channels.instagram import InstagramAdapter
from app.channels.gmail import GmailAdapter
from app.channels.registry import get_adapter, list_channels
from app.services.channel import ChannelService, _normalize_channel
from app.middleware.auth import get_current_user
from app.security import create_access_token


# ============================================================================
# Fixtures
# ============================================================================


def _make_oauth_state(user_id: str) -> str:
    token, _ = create_access_token(
        {"sub": user_id, "purpose": "channel_oauth_state"},
        expires_delta=timedelta(minutes=10),
    )
    return token

@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_user(test_db):
    """Seed a test user in the in-memory DB."""
    user = User(
        id="user-p5-001",
        email="p5user@example.com",
        name="Phase5 User",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_client(test_db, db_user):
    """Test client with authentication bypassed via dependency override."""
    app.dependency_overrides[get_current_user] = lambda: db_user
    client = TestClient(app)
    yield client
    del app.dependency_overrides[get_current_user]


@pytest.fixture(scope="function")
def unauth_client(test_db):
    """Test client without authentication override (for webhook endpoints)."""
    return TestClient(app)


# ============================================================================
# InstagramAdapter unit tests
# ============================================================================

class TestInstagramAdapter:
    def setup_method(self):
        self.adapter = InstagramAdapter()

    def test_channel_name(self):
        assert self.adapter.channel_name == "instagram_dm"

    def test_build_authorization_url_contains_required_params(self):
        with patch("app.channels.instagram.get_settings") as mock_settings:
            mock_settings.return_value.meta_app_id = "TEST_APP_ID"
            mock_settings.return_value.meta_oauth_redirect_uri = "https://api.selph.ai/v1/channels/instagram/callback"
            url = self.adapter.build_authorization_url(user_id="user-123")

        assert "TEST_APP_ID" in url
        assert "user-123" in url
        assert "instagram_manage_messages" in url
        assert "response_type=code" in url

    def test_verify_webhook_valid(self):
        with patch("app.channels.instagram.get_settings") as mock_settings:
            mock_settings.return_value.meta_verify_token = "my-verify-token"
            result = self.adapter.verify_webhook(
                mode="subscribe",
                token="my-verify-token",
                challenge="abc123",
            )
        assert result == "abc123"

    def test_verify_webhook_wrong_mode_raises(self):
        with patch("app.channels.instagram.get_settings") as mock_settings:
            mock_settings.return_value.meta_verify_token = "my-verify-token"
            with pytest.raises(ValueError, match="hub.mode"):
                self.adapter.verify_webhook("unsubscribe", "my-verify-token", "abc")

    def test_verify_webhook_wrong_token_raises(self):
        with patch("app.channels.instagram.get_settings") as mock_settings:
            mock_settings.return_value.meta_verify_token = "correct-token"
            with pytest.raises(ValueError, match="mismatch"):
                self.adapter.verify_webhook("subscribe", "wrong-token", "abc")

    def test_parse_webhook_event_text_dm(self):
        payload = {
            "object": "instagram",
            "entry": [{
                "id": "PAGE_123",
                "messaging": [{
                    "sender": {"id": "PSID_456"},
                    "recipient": {"id": "PAGE_123"},
                    "timestamp": 1712345678,
                    "message": {"mid": "mid.abc", "text": "Hello there!"},
                }],
            }],
        }
        messages = self.adapter.parse_webhook_event(payload)
        assert len(messages) == 1
        msg = messages[0]
        assert msg.channel == "instagram_dm"
        assert msg.sender_id == "PSID_456"
        assert msg.content == "Hello there!"
        assert msg.channel_metadata["page_id"] == "PAGE_123"
        assert msg.channel_metadata["message_id"] == "mid.abc"

    def test_parse_webhook_event_skips_non_text(self):
        """Sticker/attachment events have no text field — should be skipped."""
        payload = {
            "object": "instagram",
            "entry": [{
                "id": "PAGE_123",
                "messaging": [{
                    "sender": {"id": "PSID_456"},
                    "recipient": {"id": "PAGE_123"},
                    "message": {"mid": "mid.sticker", "attachments": [{"type": "image"}]},
                }],
            }],
        }
        messages = self.adapter.parse_webhook_event(payload)
        assert messages == []

    def test_parse_webhook_event_wrong_object_returns_empty(self):
        payload = {"object": "page", "entry": []}
        assert self.adapter.parse_webhook_event(payload) == []

    def test_verify_signature_valid(self):
        with patch("app.channels.instagram.get_settings") as mock_settings:
            mock_settings.return_value.meta_app_secret = "test-secret"
            payload = b'{"test": "data"}'
            mac = hmac.new(b"test-secret", payload, hashlib.sha256).hexdigest()
            assert self.adapter.verify_signature(payload, f"sha256={mac}") is True

    def test_verify_signature_invalid(self):
        with patch("app.channels.instagram.get_settings") as mock_settings:
            mock_settings.return_value.meta_app_secret = "test-secret"
            assert self.adapter.verify_signature(b"data", "sha256=badhash") is False

    def test_verify_signature_missing_header(self):
        with patch("app.channels.instagram.get_settings") as mock_settings:
            mock_settings.return_value.meta_app_secret = "test-secret"
            assert self.adapter.verify_signature(b"data", "") is False

    def test_send_reply_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        with patch("app.channels.instagram.httpx.post", return_value=mock_response):
            result = self.adapter.send_reply("PAGE_TOKEN", "PSID_456", "Great question!")
        assert result is True

    def test_send_reply_api_error_returns_false(self):
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        with patch(
            "app.channels.instagram.httpx.post",
            side_effect=httpx.HTTPStatusError("error", request=MagicMock(), response=mock_response),
        ):
            result = self.adapter.send_reply("BAD_TOKEN", "PSID_456", "Hello")
        assert result is False

    def test_exchange_code_for_token_success(self):
        """Mock the three API calls in exchange_code_for_token."""
        import httpx

        short_resp = MagicMock()
        short_resp.raise_for_status.return_value = None
        short_resp.json.return_value = {"access_token": "SHORT_TOKEN"}

        long_resp = MagicMock()
        long_resp.raise_for_status.return_value = None
        long_resp.json.return_value = {"access_token": "LONG_TOKEN", "expires_in": 5184000}

        pages_resp = MagicMock()
        pages_resp.raise_for_status.return_value = None
        pages_resp.json.return_value = {
            "data": [{"id": "PAGE_123", "name": "Test Page", "access_token": "PAGE_ACCESS_TOKEN"}]
        }

        with patch("app.channels.instagram.get_settings") as mock_settings, \
             patch("app.channels.instagram.httpx.get", side_effect=[short_resp, long_resp, pages_resp]):
            mock_settings.return_value.meta_app_id = "APP_ID"
            mock_settings.return_value.meta_app_secret = "APP_SECRET"
            mock_settings.return_value.meta_oauth_redirect_uri = "https://test/callback"

            result = self.adapter.exchange_code_for_token("AUTH_CODE")

        assert result["access_token"] == "LONG_TOKEN"
        assert len(result["pages"]) == 1
        assert result["pages"][0]["id"] == "PAGE_123"


# ============================================================================
# GmailAdapter unit tests
# ============================================================================

class TestGmailAdapter:
    def setup_method(self):
        self.adapter = GmailAdapter()

    def test_channel_name(self):
        assert self.adapter.channel_name == "gmail"

    def test_build_authorization_url_contains_required_params(self):
        with patch("app.channels.gmail.get_settings") as mock_settings:
            mock_settings.return_value.google_oauth_client_id = "GOOGLE_CLIENT_ID"
            mock_settings.return_value.google_oauth_redirect_uri = "https://api.selph.ai/v1/channels/gmail/callback"
            url = self.adapter.build_authorization_url(user_id="user-456")

        assert "GOOGLE_CLIENT_ID" in url
        assert "user-456" in url
        assert "gmail.send" in url
        assert "offline" in url
        assert "prompt=consent" in url

    def test_parse_pubsub_notification_valid(self):
        data = {"emailAddress": "user@example.com", "historyId": "12345"}
        encoded = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
        body = {"message": {"data": encoded, "messageId": "pub-001"}, "subscription": "sub-001"}
        result = self.adapter.parse_pubsub_notification(body)
        assert result["emailAddress"] == "user@example.com"
        assert result["historyId"] == "12345"

    def test_parse_pubsub_notification_missing_data(self):
        body = {"message": {"messageId": "pub-001"}, "subscription": "sub-001"}
        assert self.adapter.parse_pubsub_notification(body) is None

    def test_parse_pubsub_notification_invalid_base64(self):
        body = {"message": {"data": "!!!!invalid!!!!"}, "subscription": "sub-001"}
        assert self.adapter.parse_pubsub_notification(body) is None

    def test_extract_plain_text_body_simple(self):
        content = "Hello, world!"
        encoded = base64.urlsafe_b64encode(content.encode()).decode()
        payload = {"mimeType": "text/plain", "body": {"data": encoded}}
        result = self.adapter._extract_plain_text_body(payload)
        assert result == "Hello, world!"

    def test_extract_plain_text_body_multipart(self):
        content = "Plain text body"
        encoded = base64.urlsafe_b64encode(content.encode()).decode()
        payload = {
            "mimeType": "multipart/alternative",
            "parts": [
                {"mimeType": "text/plain", "body": {"data": encoded}},
                {"mimeType": "text/html", "body": {"data": ""}},
            ],
        }
        result = self.adapter._extract_plain_text_body(payload)
        assert result == "Plain text body"

    def test_extract_plain_text_body_empty_returns_empty_string(self):
        payload = {"mimeType": "text/html", "body": {}, "parts": []}
        assert self.adapter._extract_plain_text_body(payload) == ""

    def test_parse_webhook_event_returns_empty_list(self):
        """parse_webhook_event is intentionally a no-op for Gmail."""
        assert self.adapter.parse_webhook_event({"any": "payload"}) == []

    def test_send_reply_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        cred_value = json.dumps({"access_token": "ACCESS_TOKEN", "refresh_token": "RT", "email": "u@x.com"})
        with patch("app.channels.gmail.httpx.post", return_value=mock_response):
            result = self.adapter.send_reply(
                credential_value=cred_value,
                recipient_id="sender@example.com",
                text="Thanks for your email!",
                metadata={"subject": "Hello", "thread_id": "thread-1"},
            )
        assert result is True

    def test_send_reply_plain_token_fallback(self):
        """send_reply should work if credential_value is a plain token string (not JSON)."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        with patch("app.channels.gmail.httpx.post", return_value=mock_response):
            result = self.adapter.send_reply(
                credential_value="plain-access-token",
                recipient_id="sender@example.com",
                text="Hello!",
            )
        assert result is True

    def test_send_reply_adds_re_prefix_to_subject(self):
        """Subject should be prefixed with 'Re: ' if not already."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        cred_value = json.dumps({"access_token": "TOKEN"})
        with patch("app.channels.gmail.httpx.post", return_value=mock_response) as mock_post:
            self.adapter.send_reply(
                credential_value=cred_value,
                recipient_id="a@b.com",
                text="Reply",
                metadata={"subject": "Your Question"},
            )
        call_kwargs = mock_post.call_args[1]["json"]
        raw_decoded = base64.urlsafe_b64decode(call_kwargs["raw"] + "==").decode()
        assert "Re: Your Question" in raw_decoded

    def test_send_reply_api_error_returns_false(self):
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        with patch(
            "app.channels.gmail.httpx.post",
            side_effect=httpx.HTTPStatusError("err", request=MagicMock(), response=mock_response),
        ):
            result = self.adapter.send_reply("TOKEN", "a@b.com", "Hello")
        assert result is False

    def test_exchange_code_for_token_success(self):
        token_resp = MagicMock()
        token_resp.raise_for_status.return_value = None
        token_resp.json.return_value = {
            "access_token": "ACCESS",
            "refresh_token": "REFRESH",
            "expires_in": 3600,
            "scope": "https://www.googleapis.com/auth/gmail.send",
        }
        info_resp = MagicMock()
        info_resp.raise_for_status.return_value = None
        info_resp.json.return_value = {"email": "user@gmail.com"}

        with patch("app.channels.gmail.get_settings") as mock_settings, \
             patch("app.channels.gmail.httpx.post", return_value=token_resp), \
             patch("app.channels.gmail.httpx.get", return_value=info_resp):
            mock_settings.return_value.google_oauth_client_id = "CID"
            mock_settings.return_value.google_oauth_client_secret = "CS"
            mock_settings.return_value.google_oauth_redirect_uri = "https://test/cb"
            result = self.adapter.exchange_code_for_token("AUTH_CODE")

        assert result["access_token"] == "ACCESS"
        assert result["refresh_token"] == "REFRESH"
        assert result["email"] == "user@gmail.com"


# ============================================================================
# Channel registry tests
# ============================================================================

class TestChannelRegistry:
    def test_get_adapter_instagram(self):
        adapter = get_adapter("instagram")
        assert isinstance(adapter, InstagramAdapter)

    def test_get_adapter_instagram_dm(self):
        adapter = get_adapter("instagram_dm")
        assert isinstance(adapter, InstagramAdapter)

    def test_get_adapter_gmail(self):
        adapter = get_adapter("gmail")
        assert isinstance(adapter, GmailAdapter)

    def test_get_adapter_unknown_raises(self):
        with pytest.raises(ValueError, match="No adapter registered"):
            get_adapter("whatsapp")

    def test_list_channels_contains_known(self):
        channels = list_channels()
        assert "instagram_dm" in channels
        assert "gmail" in channels


# ============================================================================
# ChannelService unit tests (no HTTP calls)
# ============================================================================

class TestChannelService:
    def test_normalize_channel_instagram(self):
        assert _normalize_channel("instagram") == "instagram_dm"
        assert _normalize_channel("INSTAGRAM") == "instagram_dm"

    def test_normalize_channel_gmail(self):
        assert _normalize_channel("gmail") == "gmail"

    def test_upsert_credential_creates_new(self, test_db, db_user):
        cred = ChannelService.upsert_credential(
            db=test_db,
            user_id=db_user.id,
            channel="instagram_dm",
            credential_value="PAGE_TOKEN",
            scope='{"page_id": "PAGE_111"}',
        )
        assert cred.id is not None
        assert cred.channel == "instagram_dm"
        assert cred.credential_value == "PAGE_TOKEN"
        assert cred.is_active is True

    def test_upsert_credential_updates_existing(self, test_db, db_user):
        ChannelService.upsert_credential(test_db, db_user.id, "gmail", "OLD_TOKEN")
        updated = ChannelService.upsert_credential(test_db, db_user.id, "gmail", "NEW_TOKEN")
        assert updated.credential_value == "NEW_TOKEN"
        # Should only be one row
        count = test_db.query(ChannelCredential).filter(
            ChannelCredential.user_id == db_user.id,
            ChannelCredential.channel == "gmail",
        ).count()
        assert count == 1

    def test_get_credential_returns_active(self, test_db, db_user):
        ChannelService.upsert_credential(test_db, db_user.id, "gmail", "TOKEN_123")
        cred = ChannelService.get_credential(test_db, db_user.id, "gmail")
        assert cred is not None
        assert cred.credential_value == "TOKEN_123"

    def test_get_credential_returns_none_for_inactive(self, test_db, db_user):
        cred = ChannelService.upsert_credential(test_db, db_user.id, "gmail", "TOKEN")
        cred.is_active = False
        test_db.commit()
        result = ChannelService.get_credential(test_db, db_user.id, "gmail")
        assert result is None

    def test_get_credential_returns_none_for_missing(self, test_db, db_user):
        result = ChannelService.get_credential(test_db, db_user.id, "nonexistent")
        assert result is None

    def test_find_user_by_instagram_page(self, test_db, db_user):
        ChannelService.upsert_credential(
            test_db, db_user.id, "instagram_dm", "TOKEN",
            scope='{"page_id": "PAGE_999"}'
        )
        found_id = ChannelService.find_user_by_instagram_page(test_db, "PAGE_999")
        assert found_id == db_user.id

    def test_find_user_by_instagram_page_not_found(self, test_db):
        assert ChannelService.find_user_by_instagram_page(test_db, "UNKNOWN_PAGE") is None

    def test_find_user_by_gmail_address(self, test_db, db_user):
        ChannelService.upsert_credential(
            test_db, db_user.id, "gmail", "TOKEN",
            scope='{"email": "myemail@gmail.com"}'
        )
        found_id = ChannelService.find_user_by_gmail_address(test_db, "myemail@gmail.com")
        assert found_id == db_user.id

    def test_find_user_by_gmail_address_not_found(self, test_db):
        assert ChannelService.find_user_by_gmail_address(test_db, "nobody@example.com") is None

    def test_send_draft_reply_draft_not_found(self, test_db):
        result = ChannelService.send_draft_reply(test_db, "nonexistent-draft-id")
        assert result is False

    def test_send_draft_reply_no_credential(self, test_db, db_user):
        """When no channel credential exists, send_draft_reply returns False gracefully."""
        twin = Twin(
            id="twin-p5-001",
            user_id=db_user.id,
            status="active",
        )
        test_db.add(twin)
        test_db.flush()

        message = Message(
            id="msg-p5-001",
            user_id=db_user.id,
            channel="instagram_dm",
            sender_id="PSID_111",
            sender_name="Alice",
            content="Hello!",
            status="received",
            channel_metadata={"page_id": "PAGE_001"},
        )
        test_db.add(message)
        test_db.flush()

        draft = Draft(
            id="draft-p5-001",
            message_id=message.id,
            user_id=db_user.id,
            twin_id=twin.id,
            content="Hi Alice!",
            confidence_score=0.9,
            confidence_label="High",
            moderation_passed=True,
            status="approved",
        )
        test_db.add(draft)
        test_db.commit()

        result = ChannelService.send_draft_reply(test_db, draft.id)
        assert result is False

    def test_send_draft_reply_success(self, test_db, db_user):
        """When credential exists and adapter.send_reply returns True, status is 'sent'."""
        twin = Twin(id="twin-p5-002", user_id=db_user.id, status="active")
        test_db.add(twin)
        test_db.flush()

        message = Message(
            id="msg-p5-002",
            user_id=db_user.id,
            channel="instagram_dm",
            sender_id="PSID_222",
            sender_name="Bob",
            content="Hey!",
            status="received",
            channel_metadata={"page_id": "PAGE_002"},
        )
        test_db.add(message)
        test_db.flush()

        draft = Draft(
            id="draft-p5-002",
            message_id=message.id,
            user_id=db_user.id,
            twin_id=twin.id,
            content="Hey Bob!",
            confidence_score=0.85,
            confidence_label="High",
            moderation_passed=True,
            status="approved",
        )
        test_db.add(draft)

        ChannelService.upsert_credential(
            test_db, db_user.id, "instagram_dm", "VALID_PAGE_TOKEN"
        )
        test_db.commit()

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        with patch("app.channels.instagram.httpx.post", return_value=mock_response):
            result = ChannelService.send_draft_reply(test_db, draft.id)

        assert result is True
        test_db.refresh(draft)
        assert draft.status == "sent"
        assert draft.sent_response == "Hey Bob!"


# ============================================================================
# Router / API endpoint tests
# ============================================================================

class TestInstagramWebhookVerifyEndpoint:
    def test_valid_verification(self, unauth_client):
        with patch("app.routers.channels.get_settings") as mock_settings, \
             patch("app.channels.instagram.get_settings") as mock_ch_settings:
            mock_settings.return_value.meta_verify_token = "verify-secret"
            mock_settings.return_value.meta_app_secret = ""
            mock_ch_settings.return_value.meta_verify_token = "verify-secret"

            resp = unauth_client.get(
                "/v1/channels/instagram/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "verify-secret",
                    "hub.challenge": "challenge_xyz",
                },
            )
        assert resp.status_code == 200
        assert resp.text == "challenge_xyz"

    def test_invalid_token_returns_403(self, unauth_client):
        with patch("app.channels.instagram.get_settings") as mock_settings:
            mock_settings.return_value.meta_verify_token = "correct-token"
            resp = unauth_client.get(
                "/v1/channels/instagram/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "wrong-token",
                    "hub.challenge": "xyz",
                },
            )
        assert resp.status_code == 403

    def test_missing_params_returns_400(self, unauth_client):
        resp = unauth_client.get("/v1/channels/instagram/webhook")
        assert resp.status_code == 400


class TestInstagramWebhookReceiveEndpoint:
    def _make_payload(self, page_id="PAGE_123", sender_psid="PSID_456", text="Hello"):
        return {
            "object": "instagram",
            "entry": [{
                "id": page_id,
                "messaging": [{
                    "sender": {"id": sender_psid},
                    "recipient": {"id": page_id},
                    "timestamp": 1712345678,
                    "message": {"mid": "mid.test", "text": text},
                }],
            }],
        }

    def test_webhook_with_known_user_enqueues(self, unauth_client, test_db, db_user):
        ChannelService.upsert_credential(
            test_db, db_user.id, "instagram_dm", "PAGE_TOKEN",
            scope='{"page_id": "PAGE_123"}'
        )
        test_db.commit()

        with patch("app.routers.channels.get_settings") as mock_settings, \
             patch("app.routers.channels._enqueue_message_ingestion") as mock_enqueue:
            mock_settings.return_value.meta_app_secret = ""  # disable sig check
            resp = unauth_client.post(
                "/v1/channels/instagram/webhook",
                json=self._make_payload(),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["received"] is True
        assert data["queued"] == 1
        mock_enqueue.assert_called_once()
        call_kwargs = mock_enqueue.call_args[1]
        assert call_kwargs["user_id"] == db_user.id
        assert call_kwargs["channel"] == "instagram_dm"
        assert call_kwargs["sender_id"] == "PSID_456"
        assert call_kwargs["content"] == "Hello"

    def test_webhook_unknown_page_returns_zero_queued(self, unauth_client, test_db):
        with patch("app.routers.channels.get_settings") as mock_settings, \
             patch("app.routers.channels._enqueue_message_ingestion") as mock_enqueue:
            mock_settings.return_value.meta_app_secret = ""
            resp = unauth_client.post(
                "/v1/channels/instagram/webhook",
                json=self._make_payload(page_id="UNKNOWN_PAGE"),
            )
        assert resp.status_code == 200
        assert resp.json()["queued"] == 0
        mock_enqueue.assert_not_called()

    def test_webhook_signature_mismatch_returns_403(self, unauth_client):
        with patch("app.routers.channels.get_settings") as mock_settings, \
             patch("app.channels.instagram.get_settings") as mock_ch_settings:
            mock_settings.return_value.meta_app_secret = "real-secret"
            mock_ch_settings.return_value.meta_app_secret = "real-secret"
            resp = unauth_client.post(
                "/v1/channels/instagram/webhook",
                json={"object": "instagram", "entry": []},
                headers={"X-Hub-Signature-256": "sha256=badhash"},
            )
        assert resp.status_code == 403

    def test_webhook_non_text_events_return_zero_queued(self, unauth_client):
        payload = {
            "object": "instagram",
            "entry": [{
                "id": "PAGE_123",
                "messaging": [{
                    "sender": {"id": "PSID_456"},
                    "message": {"mid": "mid.sticker"},  # no text field
                }],
            }],
        }
        with patch("app.routers.channels.get_settings") as mock_settings:
            mock_settings.return_value.meta_app_secret = ""
            resp = unauth_client.post("/v1/channels/instagram/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["queued"] == 0


class TestInstagramOAuthEndpoints:
    def test_oauth_url_unconfigured_returns_503(self, auth_client):
        with patch("app.routers.channels.get_settings") as mock_settings:
            mock_settings.return_value.meta_app_id = ""
            resp = auth_client.get("/v1/channels/instagram/oauth")
        assert resp.status_code == 503

    def test_oauth_url_configured_returns_url(self, auth_client):
        with patch("app.routers.channels.get_settings") as mock_settings, \
             patch("app.channels.instagram.get_settings") as mock_ch:
            mock_settings.return_value.meta_app_id = "APP_ID_123"
            mock_ch.return_value.meta_app_id = "APP_ID_123"
            mock_ch.return_value.meta_oauth_redirect_uri = "https://test/cb"
            resp = auth_client.get("/v1/channels/instagram/oauth")
        assert resp.status_code == 200
        data = resp.json()
        assert data["channel"] == "instagram"
        assert "APP_ID_123" in data["authorization_url"]

    def test_callback_no_pages_returns_422(self, auth_client, test_db):
        adapter_result = {"access_token": "TOKEN", "expires_in": 5000, "pages": []}
        with patch.object(InstagramAdapter, "exchange_code_for_token", return_value=adapter_result):
            resp = auth_client.get(
                "/v1/channels/instagram/callback",
                params={"code": "AUTH_CODE", "state": _make_oauth_state("user-p5-001")},
            )
        assert resp.status_code == 422

    def test_callback_success_stores_credential(self, auth_client, test_db, db_user):
        adapter_result = {
            "access_token": "LONG_TOKEN",
            "expires_in": 5000,
            "pages": [{"id": "PAGE_777", "name": "My Page", "access_token": "PAGE_TOKEN_777"}],
        }
        with patch.object(InstagramAdapter, "exchange_code_for_token", return_value=adapter_result):
            resp = auth_client.get(
                "/v1/channels/instagram/callback",
                params={"code": "AUTH_CODE", "state": _make_oauth_state(db_user.id)},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is True
        assert data["page_count"] == 1

        cred = ChannelService.get_credential(test_db, db_user.id, "instagram_dm")
        assert cred is not None
        assert cred.credential_value == "PAGE_TOKEN_777"

    def test_callback_token_exchange_failure_returns_502(self, auth_client, test_db, db_user):
        with patch.object(InstagramAdapter, "exchange_code_for_token", side_effect=Exception("API down")):
            resp = auth_client.get(
                "/v1/channels/instagram/callback",
                params={"code": "BAD_CODE", "state": _make_oauth_state(db_user.id)},
            )
        assert resp.status_code == 502

    def test_callback_invalid_state_returns_400(self, auth_client):
        resp = auth_client.get(
            "/v1/channels/instagram/callback",
            params={"code": "AUTH_CODE", "state": "raw-user-id-not-signed"},
        )
        assert resp.status_code == 400


class TestGmailOAuthEndpoints:
    def test_oauth_url_unconfigured_returns_503(self, auth_client):
        with patch("app.routers.channels.get_settings") as mock_settings:
            mock_settings.return_value.google_oauth_client_id = ""
            resp = auth_client.get("/v1/channels/gmail/oauth")
        assert resp.status_code == 503

    def test_oauth_url_configured_returns_url(self, auth_client):
        with patch("app.routers.channels.get_settings") as mock_settings, \
             patch("app.channels.gmail.get_settings") as mock_ch:
            mock_settings.return_value.google_oauth_client_id = "GCID_123"
            mock_ch.return_value.google_oauth_client_id = "GCID_123"
            mock_ch.return_value.google_oauth_redirect_uri = "https://test/cb"
            resp = auth_client.get("/v1/channels/gmail/oauth")
        assert resp.status_code == 200
        data = resp.json()
        assert data["channel"] == "gmail"
        assert "GCID_123" in data["authorization_url"]

    def test_callback_success_stores_credential(self, auth_client, test_db, db_user):
        token_data = {
            "access_token": "GMAIL_ACCESS",
            "refresh_token": "GMAIL_REFRESH",
            "expires_in": 3600,
            "email": "user@gmail.com",
            "scope": "https://www.googleapis.com/auth/gmail.send",
        }
        with patch.object(GmailAdapter, "exchange_code_for_token", return_value=token_data), \
             patch("app.routers.channels.get_settings") as mock_settings, \
             patch.object(GmailAdapter, "setup_push_notifications", return_value={}):
            mock_settings.return_value.google_pubsub_topic = "projects/test/topics/gmail"
            resp = auth_client.get(
                "/v1/channels/gmail/callback",
                params={"code": "AUTH_CODE", "state": _make_oauth_state(db_user.id)},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is True
        assert data["email"] == "user@gmail.com"

        cred = ChannelService.get_credential(test_db, db_user.id, "gmail")
        assert cred is not None
        cred_data = json.loads(cred.credential_value)
        assert cred_data["access_token"] == "GMAIL_ACCESS"
        assert cred_data["email"] == "user@gmail.com"

    def test_callback_token_exchange_failure_returns_502(self, auth_client, test_db, db_user):
        with patch.object(GmailAdapter, "exchange_code_for_token", side_effect=Exception("OAuth failed")):
            resp = auth_client.get(
                "/v1/channels/gmail/callback",
                params={"code": "BAD_CODE", "state": _make_oauth_state(db_user.id)},
            )
        assert resp.status_code == 502

    def test_callback_invalid_state_returns_400(self, auth_client):
        resp = auth_client.get(
            "/v1/channels/gmail/callback",
            params={"code": "AUTH_CODE", "state": "raw-user-id-not-signed"},
        )
        assert resp.status_code == 400


class TestGmailWebhookEndpoint:
    def _make_pubsub_body(self, email="user@gmail.com", history_id="9999"):
        data = json.dumps({"emailAddress": email, "historyId": history_id})
        encoded = base64.urlsafe_b64encode(data.encode()).decode()
        return {"message": {"data": encoded, "messageId": "pub-111"}, "subscription": "sub-111"}

    def test_webhook_unknown_email_returns_zero_queued(self, unauth_client, test_db):
        resp = unauth_client.post(
            "/v1/channels/gmail/webhook",
            json=self._make_pubsub_body("nobody@example.com"),
        )
        assert resp.status_code == 200
        assert resp.json()["queued"] == 0

    def test_webhook_malformed_body_returns_zero_queued(self, unauth_client):
        body = {"message": {"messageId": "pub-001"}}  # no data field
        resp = unauth_client.post("/v1/channels/gmail/webhook", json=body)
        assert resp.status_code == 200
        assert resp.json()["queued"] == 0

    def test_webhook_rejects_invalid_shared_secret_when_configured(self, unauth_client):
        with patch("app.routers.channels.get_settings") as mock_settings:
            mock_settings.return_value.google_webhook_secret = "expected-secret"
            resp = unauth_client.post(
                "/v1/channels/gmail/webhook",
                json=self._make_pubsub_body("user@gmail.com"),
                headers={"X-Webhook-Token": "wrong-secret"},
            )
        assert resp.status_code == 403

    def test_webhook_accepts_shared_secret_when_configured(self, unauth_client):
        with patch("app.routers.channels.get_settings") as mock_settings:
            mock_settings.return_value.google_webhook_secret = "expected-secret"
            resp = unauth_client.post(
                "/v1/channels/gmail/webhook",
                json=self._make_pubsub_body("nobody@example.com"),
                headers={"X-Webhook-Token": "expected-secret"},
            )
        assert resp.status_code == 200
        assert resp.json()["queued"] == 0

    def test_webhook_known_user_enqueues_messages(self, unauth_client, test_db, db_user):
        ChannelService.upsert_credential(
            test_db, db_user.id, "gmail",
            json.dumps({"access_token": "AT", "refresh_token": "RT", "email": "user@gmail.com"}),
            scope='{"email": "user@gmail.com"}'
        )
        test_db.commit()

        from app.channels.base import NormalizedMessage
        fake_messages = [
            NormalizedMessage(
                channel="gmail",
                sender_id="sender@example.com",
                sender_name="Sender",
                content="Hey, question here",
                channel_metadata={"message_id": "msg-abc", "thread_id": "thr-1", "subject": "Question"},
            )
        ]

        with patch.object(GmailAdapter, "fetch_new_messages", return_value=fake_messages), \
             patch("app.routers.channels._enqueue_message_ingestion") as mock_enqueue:
            resp = unauth_client.post(
                "/v1/channels/gmail/webhook",
                json=self._make_pubsub_body("user@gmail.com", "9999"),
            )

        assert resp.status_code == 200
        assert resp.json()["queued"] == 1
        mock_enqueue.assert_called_once()
        call_kwargs = mock_enqueue.call_args[1]
        assert call_kwargs["user_id"] == db_user.id
        assert call_kwargs["channel"] == "gmail"


class TestLegacyConnectEndpoints:
    def test_instagram_connect_legacy(self, auth_client, test_db, db_user):
        resp = auth_client.post(
            "/v1/channels/instagram/connect",
            json={"credential_value": "ig_token_123", "scope": None},
        )
        assert resp.status_code == 200
        assert resp.json()["connected"] is True
        cred = ChannelService.get_credential(test_db, db_user.id, "instagram_dm")
        assert cred.credential_value == "ig_token_123"

    def test_gmail_connect_legacy(self, auth_client, test_db, db_user):
        resp = auth_client.post(
            "/v1/channels/gmail/connect",
            json={"credential_value": "gmail_token_456"},
        )
        assert resp.status_code == 200
        assert resp.json()["connected"] is True
        cred = ChannelService.get_credential(test_db, db_user.id, "gmail")
        assert cred.credential_value == "gmail_token_456"


class TestListConnectedChannels:
    def test_empty_for_new_user(self, auth_client):
        resp = auth_client.get("/v1/channels/connected")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_connected_channels(self, auth_client, test_db, db_user):
        ChannelService.upsert_credential(test_db, db_user.id, "gmail", "TOKEN")
        test_db.commit()
        resp = auth_client.get("/v1/channels/connected")
        assert resp.status_code == 200
        channels = resp.json()
        assert any(c["channel"] == "gmail" and c["connected"] for c in channels)


class TestDisconnectChannel:
    def test_disconnect_connected_channel(self, auth_client, test_db, db_user):
        ChannelService.upsert_credential(test_db, db_user.id, "instagram_dm", "TOKEN")
        test_db.commit()
        resp = auth_client.post("/v1/channels/instagram/disconnect")
        assert resp.status_code == 200
        assert resp.json()["connected"] is False

    def test_disconnect_not_connected_returns_404(self, auth_client):
        resp = auth_client.post("/v1/channels/gmail/disconnect")
        assert resp.status_code == 404

    def test_disconnect_unsupported_channel_returns_400(self, auth_client):
        resp = auth_client.post("/v1/channels/twitter/disconnect")
        assert resp.status_code == 400


class TestSendReplyEndpoint:
    def test_send_reply_draft_not_found(self, auth_client):
        resp = auth_client.post(
            "/v1/channels/send-reply",
            json={"draft_id": "nonexistent-draft"},
        )
        assert resp.status_code == 404

    def test_send_reply_wrong_status_returns_409(self, auth_client, test_db, db_user):
        twin = Twin(id="twin-sr-001", user_id=db_user.id, status="active")
        test_db.add(twin)
        test_db.flush()
        message = Message(
            id="msg-sr-001", user_id=db_user.id, channel="instagram_dm",
            sender_id="S1", sender_name="S", content="Hi", status="received",
            channel_metadata={},
        )
        test_db.add(message)
        test_db.flush()
        draft = Draft(
            id="draft-sr-001", message_id=message.id, user_id=db_user.id,
            twin_id=twin.id, content="Hi back", confidence_score=0.8,
            confidence_label="High", moderation_passed=True,
            status="pending_approval",  # not eligible for send
        )
        test_db.add(draft)
        test_db.commit()

        resp = auth_client.post("/v1/channels/send-reply", json={"draft_id": "draft-sr-001"})
        assert resp.status_code == 409

    def test_send_reply_approved_draft(self, auth_client, test_db, db_user):
        twin = Twin(id="twin-sr-002", user_id=db_user.id, status="active")
        test_db.add(twin)
        test_db.flush()
        message = Message(
            id="msg-sr-002", user_id=db_user.id, channel="instagram_dm",
            sender_id="PSID_SR", sender_name="SR", content="Hey!", status="received",
            channel_metadata={"page_id": "PAGE_SR"},
        )
        test_db.add(message)
        test_db.flush()
        draft = Draft(
            id="draft-sr-002", message_id=message.id, user_id=db_user.id,
            twin_id=twin.id, content="Hey there!", confidence_score=0.9,
            confidence_label="High", moderation_passed=True, status="approved",
        )
        test_db.add(draft)
        ChannelService.upsert_credential(test_db, db_user.id, "instagram_dm", "PAGE_TOKEN")
        test_db.commit()

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        with patch("app.channels.instagram.httpx.post", return_value=mock_response):
            resp = auth_client.post("/v1/channels/send-reply", json={"draft_id": "draft-sr-002"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["sent"] is True
        assert data["draft_id"] == "draft-sr-002"
