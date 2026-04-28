"""
Instagram DM channel adapter.
Uses Meta Graph API v19.0 for OAuth, webhook verification, and message delivery.

Prerequisites:
  - Instagram Business Account connected to a Meta App
  - Meta App configured with instagram_messaging webhook subscription
  - META_APP_ID, META_APP_SECRET, META_VERIFY_TOKEN, META_OAUTH_REDIRECT_URI set
"""

import hashlib
import hmac
import json
import logging
import urllib.parse

import httpx

from app.channels.base import ChannelAdapter, NormalizedMessage
from app.config import get_settings

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
FACEBOOK_OAUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"

# OAuth scopes required for Instagram DM management
INSTAGRAM_SCOPES = [
    "instagram_basic",
    "instagram_manage_messages",
    "pages_messaging",
    "pages_show_list",
    "pages_manage_metadata",
]


class InstagramAdapter(ChannelAdapter):
    """
    Channel adapter for Instagram DMs via Meta Graph API.

    OAuth flow:
      1. build_authorization_url(user_id) → redirect user to Meta login
      2. exchange_code_for_token(code)    → short-lived → long-lived token, fetch pages
      3. Store credential_value = page access token, scope = JSON(page_id=...)

    Incoming messages:
      GET  /channels/instagram/webhook  → Meta hub.challenge verification
      POST /channels/instagram/webhook  → Receive DM events, normalize, enqueue

    Outgoing replies:
      send_reply(page_access_token, psid, text)
    """

    @property
    def channel_name(self) -> str:
        return "instagram_dm"

    def build_authorization_url(self, user_id: str) -> str:
        """
        Build Meta OAuth dialog URL.
        The 'state' parameter carries the SELPH user_id so the callback can
        identify which user connected their account.
        """
        settings = get_settings()
        params = {
            "client_id": settings.meta_app_id,
            "redirect_uri": settings.meta_oauth_redirect_uri,
            "scope": ",".join(INSTAGRAM_SCOPES),
            "response_type": "code",
            "state": user_id,
        }
        return f"{FACEBOOK_OAUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> dict:
        """
        Exchange auth code → short-lived user token → long-lived token (60 days).
        Also fetches the list of Pages so callers can store the page access token
        and page ID for webhook routing.

        Returns:
            {
                "access_token":  str,   # long-lived user access token
                "expires_in":    int,   # seconds (~5184000 = 60 days)
                "pages":         list,  # [{ id, name, access_token, ... }]
            }
        """
        settings = get_settings()

        # Step 1: Exchange code for short-lived user token
        resp = httpx.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "redirect_uri": settings.meta_oauth_redirect_uri,
                "code": code,
            },
            timeout=15,
        )
        resp.raise_for_status()
        short_lived = resp.json()
        short_token = short_lived["access_token"]

        # Step 2: Exchange for long-lived user token
        resp2 = httpx.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "fb_exchange_token": short_token,
            },
            timeout=15,
        )
        resp2.raise_for_status()
        long_lived = resp2.json()

        # Step 3: Fetch connected pages (Instagram Business Account is linked to a Page)
        pages_resp = httpx.get(
            f"{GRAPH_API_BASE}/me/accounts",
            params={
                "access_token": long_lived["access_token"],
                "fields": "id,name,access_token,instagram_business_account",
            },
            timeout=15,
        )
        pages_resp.raise_for_status()
        pages = pages_resp.json().get("data", [])

        return {
            "access_token": long_lived["access_token"],
            "expires_in": long_lived.get("expires_in", 5183944),
            "pages": pages,
        }

    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        """
        Validate Meta webhook verification GET request.
        Meta sends hub.mode=subscribe, hub.verify_token, hub.challenge.
        We respond with hub.challenge if the verify token matches.

        Raises ValueError if validation fails.
        Returns the challenge string to echo back.
        """
        settings = get_settings()
        if mode != "subscribe":
            raise ValueError(f"Unexpected hub.mode: '{mode}' (expected 'subscribe')")
        if token != settings.meta_verify_token:
            raise ValueError("hub.verify_token mismatch — webhook verification rejected")
        return challenge

    def verify_signature(self, payload: bytes, signature_header: str) -> bool:
        """
        Validate X-Hub-Signature-256 header on inbound Meta webhook payloads.
        Ensures the POST body was sent by Meta and not tampered with.

        Args:
            payload:          Raw request body bytes.
            signature_header: Value of the 'X-Hub-Signature-256' header.

        Returns:
            True if signature is valid, False otherwise.
        """
        settings = get_settings()
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        mac = hmac.new(
            settings.meta_app_secret.encode(),
            payload,
            hashlib.sha256,
        )
        expected = mac.hexdigest()
        received = signature_header[len("sha256="):]
        return hmac.compare_digest(expected, received)

    def parse_webhook_event(self, body: dict) -> list[NormalizedMessage]:
        """
        Parse Meta Graph API messaging webhook payload.

        Meta sends:
          {
            "object": "instagram",
            "entry": [{
              "id": "PAGE_ID",
              "messaging": [{
                "sender": { "id": "PSID" },
                "recipient": { "id": "PAGE_ID" },
                "message": { "mid": "...", "text": "Hello!" }
              }]
            }]
          }

        Returns list of NormalizedMessage for text DMs only.
        Non-text attachments (stickers, images, reactions) are silently skipped.
        """
        messages: list[NormalizedMessage] = []

        if body.get("object") not in ("instagram", "page"):
            return messages

        for entry in body.get("entry", []):
            page_id = entry.get("id", "")
            for messaging in entry.get("messaging", []):
                msg = messaging.get("message", {})
                text = msg.get("text", "").strip()
                if not text:
                    continue  # skip non-text events (stickers, reactions, etc.)

                sender_id = messaging.get("sender", {}).get("id", "")
                if not sender_id:
                    continue

                messages.append(NormalizedMessage(
                    channel="instagram_dm",
                    sender_id=sender_id,
                    sender_name=sender_id,  # PSID only; name requires separate People API call
                    content=text,
                    channel_metadata={
                        "page_id": page_id,
                        "message_id": msg.get("mid"),
                        "timestamp": messaging.get("timestamp"),
                    },
                ))

        return messages

    def send_reply(
        self,
        credential_value: str,
        recipient_id: str,
        text: str,
        metadata: dict | None = None,
    ) -> bool:
        """
        Send a DM reply via Meta Graph API Messenger Send API.

        Args:
            credential_value: Page access token (not user token).
            recipient_id:     Instagram-scoped user ID (PSID).
            text:             Reply text (max 1000 chars for Instagram DMs).
            metadata:         Unused for Instagram; kept for interface compatibility.

        Returns:
            True on success, False on failure.
        """
        try:
            resp = httpx.post(
                f"{GRAPH_API_BASE}/me/messages",
                params={"access_token": credential_value},
                json={
                    "recipient": {"id": recipient_id},
                    "message": {"text": text[:1000]},  # Instagram DM limit
                },
                timeout=15,
            )
            resp.raise_for_status()
            logger.info("Instagram DM sent to PSID=%s", recipient_id)
            return True
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Instagram send_reply HTTP error: %s %s",
                exc.response.status_code,
                exc.response.text,
            )
            return False
        except Exception as exc:
            logger.error("Instagram send_reply failed: %s", exc)
            return False
