"""
Abstract channel adapter interface.
All channel integrations (Instagram, Gmail, etc.) implement this contract.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class NormalizedMessage:
    """
    Channel-agnostic message representation.
    The twin engine and message ingestion pipeline work exclusively with this type,
    never with raw channel payloads.
    """

    channel: str
    """Canonical channel name: 'instagram_dm' | 'gmail'"""

    sender_id: str
    """External identifier for the sender (Instagram PSID, Gmail address, etc.)"""

    sender_name: str
    """Human-readable sender name."""

    content: str
    """Decoded plain-text message body."""

    channel_metadata: dict = field(default_factory=dict)
    """
    Raw, channel-specific metadata preserved for reply routing.
    Instagram: { page_id, message_id, timestamp }
    Gmail:     { message_id, thread_id, subject, from }
    """


class ChannelAdapter(ABC):
    """
    Abstract base class for all channel integrations.

    Each channel must implement:
    - build_authorization_url  — generate OAuth dialog URL
    - exchange_code_for_token  — exchange auth code for OAuth tokens
    - parse_webhook_event      — decode raw webhook payload → NormalizedMessage list
    - send_reply               — send approved draft back through the channel
    """

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Canonical channel identifier (e.g. 'instagram_dm', 'gmail')."""

    @abstractmethod
    def build_authorization_url(self, user_id: str) -> str:
        """
        Return the OAuth authorization URL the user should be redirected to.

        Args:
            user_id: SELPH user ID, embedded as 'state' parameter for callback validation.

        Returns:
            Absolute authorization URL string.
        """

    @abstractmethod
    def exchange_code_for_token(self, code: str) -> dict:
        """
        Exchange an authorization code for OAuth tokens.

        Args:
            code: Authorization code from the OAuth callback.

        Returns:
            Dict with at minimum: access_token, plus channel-specific fields.
            Raises httpx.HTTPStatusError on API failure.
        """

    @abstractmethod
    def parse_webhook_event(self, body: dict) -> list[NormalizedMessage]:
        """
        Extract normalized messages from a raw inbound webhook payload.

        Args:
            body: Parsed JSON body from the webhook POST request.

        Returns:
            List of NormalizedMessage (may be empty if no actionable messages).
        """

    @abstractmethod
    def send_reply(
        self,
        credential_value: str,
        recipient_id: str,
        text: str,
        metadata: dict | None = None,
    ) -> bool:
        """
        Send an approved reply through this channel.

        Args:
            credential_value: OAuth access token (or equivalent) from ChannelCredential.
            recipient_id:     External sender ID from NormalizedMessage.sender_id.
            text:             Plain-text reply content.
            metadata:         channel_metadata from the original NormalizedMessage,
                              used for threading (e.g., Gmail thread_id, subject).

        Returns:
            True on success, False on failure (errors are logged internally).
        """
