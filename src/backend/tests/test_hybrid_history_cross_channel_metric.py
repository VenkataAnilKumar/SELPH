"""Additional unit test for hybrid history cross-channel metric (ADR-002)."""
from __future__ import annotations

from datetime import datetime, UTC
from unittest.mock import MagicMock

from app.services.twin_engine import TwinEngineService
from app.models.message import Message


def _make_message(content: str, channel: str = "gmail", rank_hint: int = 0) -> Message:
    msg = MagicMock(spec=Message)
    msg.content = content
    msg.id = f"msg-{rank_hint}"
    msg.created_at = datetime.now(UTC)
    msg.channel = channel
    return msg


def test_load_hybrid_history_emits_cross_channel_included_metric(caplog):
    """When cross_channel is enabled and selected messages come from other channels, emit the metric."""
    pool = [
        _make_message("pro plan pricing details", channel="instagram", rank_hint=0),
        _make_message("unrelated weather", channel="gmail", rank_hint=1),
    ]
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = pool

    incoming_msg = _make_message("pro plan?")
    incoming_msg.sender_id = "s"
    incoming_msg.channel = "gmail"
    incoming_msg.user_id = "u"
    incoming_msg.id = "in"

    from app.config import settings
    original = settings.hybrid_history_cross_channel
    try:
        settings.hybrid_history_cross_channel = True
        with caplog.at_level("INFO"):
            result = TwinEngineService._load_hybrid_history(mock_db, incoming_msg, "u")
        assert len(result) >= 1
        assert any("hybrid_history_cross_channel_included" in rec.message for rec in caplog.records)
    finally:
        settings.hybrid_history_cross_channel = original
