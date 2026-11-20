"""Unit test for channel label in hybrid history prompt when cross-channel is enabled."""
from __future__ import annotations

from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock

from app.services.twin_engine import TwinEngineService
from app.models.message import Message


def test_build_history_prompt_includes_channel_when_cross_channel_enabled():
    """When hybrid_history_cross_channel is true, prompt lines include the channel."""
    msg = MagicMock(spec=Message)
    msg.content = "Earlier question about pricing"
    msg.created_at = datetime.now(UTC) - timedelta(hours=3)
    msg.channel = "instagram"

    from app.config import settings
    original = settings.hybrid_history_cross_channel
    try:
        settings.hybrid_history_cross_channel = True
        prompt = TwinEngineService._build_history_prompt([msg])
        assert "| instagram]" in prompt
        assert "[3h ago | instagram]" in prompt or "[2h ago | instagram]" in prompt or "[4h ago | instagram]" in prompt
    finally:
        settings.hybrid_history_cross_channel = original


def test_build_history_prompt_omits_channel_when_cross_channel_disabled():
    """When hybrid_history_cross_channel is false, prompt lines do not include channel."""
    msg = MagicMock(spec=Message)
    msg.content = "Earlier question about pricing"
    msg.created_at = datetime.now(UTC) - timedelta(hours=3)
    msg.channel = "instagram"

    from app.config import settings
    original = settings.hybrid_history_cross_channel
    try:
        settings.hybrid_history_cross_channel = False
        prompt = TwinEngineService._build_history_prompt([msg])
        assert "| instagram]" not in prompt
        assert "[3h ago]" in prompt or "[2h ago]" in prompt or "[4h ago]" in prompt
    finally:
        settings.hybrid_history_cross_channel = original
