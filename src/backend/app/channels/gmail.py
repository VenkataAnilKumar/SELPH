"""
Gmail channel adapter.
Uses Google OAuth 2.0 for authorization, Gmail API for reading/sending,
and Google Cloud Pub/Sub push subscriptions for real-time new-email delivery.

Prerequisites:
  - Google Cloud project with Gmail API + Pub/Sub API enabled
  - OAuth 2.0 credentials (type: Web application)
  - Pub/Sub topic created and SELPH webhook URL configured as push subscriber
  - GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET,
    GOOGLE_OAUTH_REDIRECT_URI, GOOGLE_PUBSUB_TOPIC set in env
"""

import base64
import json
import logging
import urllib.parse
from email.mime.text import MIMEText

import httpx

from app.channels.base import ChannelAdapter, NormalizedMessage
from app.config import get_settings

logger = logging.getLogger(__name__)

GMAIL_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Required OAuth scopes for Gmail DM-style usage
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
]


class GmailAdapter(ChannelAdapter):
    """
    Channel adapter for Gmail via Google OAuth 2.0 + Pub/Sub push notifications.

    OAuth flow:
      1. build_authorization_url(user_id) → redirect user to Google consent screen
      2. exchange_code_for_token(code)    → access + refresh tokens, fetch user email
      3. setup_push_notifications(token)  → register gmail.watch() for INBOX label
      4. Store credential_value = JSON(access_token, refresh_token, email)

    Incoming messages (real-time, not polling):
      POST /channels/gmail/webhook  → Pub/Sub push notification
        decode → historyId → Gmail History API → fetch new message bodies

    Outgoing replies:
      send_reply(credential_json, sender_email, text, metadata)
    """

    @property
    def channel_name(self) -> str:
        return "gmail"

    def build_authorization_url(self, user_id: str) -> str:
        """
        Build Google OAuth2 authorization URL.
        Requests offline access to receive a refresh token for long-lived credentials.
        """
        settings = get_settings()
        params = {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": settings.google_oauth_redirect_uri,
            "response_type": "code",
            "scope": " ".join(GMAIL_SCOPES),
            "access_type": "offline",
            "prompt": "consent",   # Force refresh_token to be returned on every consent
            "state": user_id,
        }
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> dict:
        """
        Exchange authorization code for access + refresh tokens.
        Also fetches the authenticated user's email address.

        Returns:
            {
                "access_token":  str,
                "refresh_token": str,   # present only on first authorization or re-consent
                "expires_in":    int,   # seconds (typically 3600)
                "email":         str,   # authenticated Google account email
                "scope":         str,   # granted scope string
            }
        """
        settings = get_settings()
        resp = httpx.post(
            GMAIL_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": settings.google_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
        resp.raise_for_status()
        tokens = resp.json()

        # Fetch the authenticated user's email for user-to-credential mapping
        email_resp = httpx.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            timeout=15,
        )
        email_resp.raise_for_status()
        user_info = email_resp.json()

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token", ""),
            "expires_in": tokens.get("expires_in", 3600),
            "email": user_info.get("email", ""),
            "scope": tokens.get("scope", ""),
        }

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Use a refresh token to obtain a new short-lived access token.
        Call this when an API request returns 401 Unauthorized.

        Returns:
            New access token string.
        """
        settings = get_settings()
        resp = httpx.post(
            GMAIL_TOKEN_URL,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def setup_push_notifications(self, access_token: str, user_email: str = "me") -> dict:
        """
        Register gmail.watch() to receive Pub/Sub push notifications for INBOX events.
        Must be called once after OAuth authorization and renewed every ~7 days.

        Args:
            access_token: Valid Gmail API access token.
            user_email:   Gmail user identifier ('me' uses the authenticated user).

        Returns:
            { historyId: str, expiration: str }  from Gmail API.
        """
        settings = get_settings()
        resp = httpx.post(
            f"{GMAIL_API_BASE}/users/{user_email}/watch",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "topicName": settings.google_pubsub_topic,
                "labelIds": ["INBOX"],
                "labelFilterBehavior": "INCLUDE",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()  # { historyId, expiration }

    def parse_pubsub_notification(self, body: dict) -> dict | None:
        """
        Decode a Google Pub/Sub push notification envelope.

        Google Pub/Sub sends:
          {
            "message": {
              "data": "<base64url-encoded JSON: { emailAddress, historyId }>",
              "messageId": "...",
              "publishTime": "..."
            },
            "subscription": "..."
          }

        Returns:
            { emailAddress: str, historyId: str } or None on parse failure.
        """
        message = body.get("message", {})
        data_b64 = message.get("data")
        if not data_b64:
            logger.warning("Pub/Sub notification has no 'data' field")
            return None

        try:
            # Pub/Sub uses base64url without padding; add padding to be safe
            padded = data_b64 + "=="
            decoded = base64.urlsafe_b64decode(padded).decode("utf-8")
            return json.loads(decoded)
        except Exception as exc:
            logger.error("Failed to decode Pub/Sub data: %s", exc)
            return None

    def fetch_new_messages(
        self, access_token: str, history_id: str, user_email: str = "me"
    ) -> list[NormalizedMessage]:
        """
        Use Gmail History API to fetch emails added since a given historyId.
        Only retrieves messages added to INBOX (skips sent items, drafts, etc.).

        Args:
            access_token: Valid Gmail API access token.
            history_id:   Starting historyId from Pub/Sub notification.
            user_email:   Gmail user identifier.

        Returns:
            List of NormalizedMessage (may be empty).
        """
        messages: list[NormalizedMessage] = []
        try:
            resp = httpx.get(
                f"{GMAIL_API_BASE}/users/{user_email}/history",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "startHistoryId": history_id,
                    "historyTypes": "messageAdded",
                    "labelId": "INBOX",
                },
                timeout=15,
            )
            resp.raise_for_status()
            history_data = resp.json()

            for record in history_data.get("history", []):
                for added in record.get("messagesAdded", []):
                    msg_id = added["message"]["id"]
                    normalized = self._fetch_and_normalize_message(
                        access_token, user_email, msg_id
                    )
                    if normalized:
                        messages.append(normalized)

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Gmail history fetch HTTP error %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
        except Exception as exc:
            logger.error("Gmail fetch_new_messages failed: %s", exc)

        return messages

    def _fetch_and_normalize_message(
        self, access_token: str, user_email: str, message_id: str
    ) -> NormalizedMessage | None:
        """
        Fetch a single Gmail message by ID and normalize it.
        Returns None if the message cannot be fetched or has no plain-text body.
        """
        try:
            resp = httpx.get(
                f"{GMAIL_API_BASE}/users/{user_email}/messages/{message_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"format": "full"},
                timeout=15,
            )
            resp.raise_for_status()
            msg = resp.json()

            headers_raw = msg.get("payload", {}).get("headers", [])
            headers = {h["name"].lower(): h["value"] for h in headers_raw}

            subject = headers.get("subject", "(no subject)")
            from_header = headers.get("from", "")

            # Parse "Display Name <email@example.com>" or plain "email@example.com"
            sender_email = from_header
            sender_name = from_header
            if "<" in from_header and ">" in from_header:
                name_part, email_part = from_header.rsplit("<", 1)
                sender_name = name_part.strip().strip('"')
                sender_email = email_part.rstrip(">").strip()

            body_text = self._extract_plain_text_body(msg.get("payload", {}))
            if not body_text:
                logger.debug("Gmail message %s has no plain-text body — skipping", message_id)
                return None

            return NormalizedMessage(
                channel="gmail",
                sender_id=sender_email,
                sender_name=sender_name or sender_email,
                content=body_text,
                channel_metadata={
                    "message_id": message_id,
                    "thread_id": msg.get("threadId"),
                    "subject": subject,
                    "from": from_header,
                },
            )
        except Exception as exc:
            logger.error("Failed to fetch/normalize Gmail message %s: %s", message_id, exc)
            return None

    def _extract_plain_text_body(self, payload: dict) -> str:
        """
        Recursively extract the first text/plain part from a Gmail message payload.
        Handles simple messages and multipart MIME structures.
        """
        mime_type = payload.get("mimeType", "")

        if mime_type == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                # Gmail uses base64url encoding; add padding
                return (
                    base64.urlsafe_b64decode(data + "==")
                    .decode("utf-8", errors="replace")
                    .strip()
                )

        for part in payload.get("parts", []):
            text = self._extract_plain_text_body(part)
            if text:
                return text

        return ""

    def parse_webhook_event(self, body: dict) -> list[NormalizedMessage]:
        """
        Satisfies the abstract interface.
        For Gmail, inbound events arrive as Pub/Sub push notifications and require
        two additional calls (parse_pubsub_notification + fetch_new_messages).
        The router handles this multi-step flow directly; this method is not used
        in normal operation but returns empty list to satisfy the interface.
        """
        return []

    def send_reply(
        self,
        credential_value: str,
        recipient_id: str,
        text: str,
        metadata: dict | None = None,
    ) -> bool:
        """
        Send a reply email via Gmail API.

        Args:
            credential_value: JSON string with { access_token, refresh_token, email }.
                              OR plain access token string (legacy / fallback).
            recipient_id:     Sender's email address (from NormalizedMessage.sender_id).
            text:             Plain-text reply body.
            metadata:         channel_metadata from original message.
                              Uses 'subject', 'thread_id', 'message_id' for threading.

        Returns:
            True on success, False on failure.
        """
        metadata = metadata or {}

        # credential_value is stored as JSON: { access_token, refresh_token, email }
        try:
            cred_data = json.loads(credential_value)
            access_token = cred_data.get("access_token", credential_value)
        except (json.JSONDecodeError, TypeError):
            access_token = credential_value

        subject = metadata.get("subject", "(no subject)")
        thread_id = metadata.get("thread_id")
        original_message_id = metadata.get("message_id")

        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        # Build RFC 2822 email
        mime_msg = MIMEText(text, "plain")
        mime_msg["To"] = recipient_id
        mime_msg["Subject"] = subject
        if original_message_id:
            # RFC 2822 threading headers
            mime_msg["In-Reply-To"] = original_message_id
            mime_msg["References"] = original_message_id

        raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode("utf-8")
        body_payload: dict = {"raw": raw}
        if thread_id:
            body_payload["threadId"] = thread_id

        try:
            resp = httpx.post(
                f"{GMAIL_API_BASE}/users/me/messages/send",
                headers={"Authorization": f"Bearer {access_token}"},
                json=body_payload,
                timeout=15,
            )
            resp.raise_for_status()
            logger.info("Gmail reply sent to %s", recipient_id)
            return True
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Gmail send_reply HTTP error %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            return False
        except Exception as exc:
            logger.error("Gmail send_reply failed: %s", exc)
            return False
