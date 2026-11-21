"""Unit test for sender name label in hybrid history prompt."""
from __future__ import annotations

from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock

from app.services.twin_engine import TwinEngineService
from app.models.message import Message


def test_build_history_prompt_includes_sender_name_when_available():
    """History prompt lines include the sender_name when present."""
    msg = MagicMock(spec=Message)
    msg.content = "Earlier question about pricing"
    msg.created_at = datetime.now(UTC) - timedelta(hours=3)
    msg.channel = "gmail"
    msg.sender_name = "Alice"

    prompt = TwinEngineService._build_history_prompt([msg])
    assert "| Alice]" in prompt
    assert "Alice" in prompt
    assert "Earlier question about pricing" in prompt


def test_build_history_prompt_omits_sender_when_missing():
    """History prompt lines omit the sender part when sender_name is empty."""
    msg = MagicMock(spec=Message)
    msg.content = "Earlier question about pricing"
    msg.created_at = datetime.now(UTC) - timedelta(hours=3)
    msg.channel = "gmail"
    msg.sender_name = ""

    prompt = TwinEngineService._build_history_prompt([msg])
    assert "| ]" not in prompt
    assert "Earlier question about pricing" in prompt
