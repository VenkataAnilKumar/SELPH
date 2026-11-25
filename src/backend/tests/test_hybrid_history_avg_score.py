"""Unit test for average score in hybrid history selection metric (ADR-002)."""
from __future__ import annotations

from unittest.mock import MagicMock

from app.services.twin_engine import TwinEngineService
from app.models.message import Message


def _make_message(content: str, rank_hint: int = 0) -> Message:
    msg = MagicMock(spec=Message)
    msg.content = content
    msg.id = f"msg-{rank_hint}"
    msg.created_at = None
    return msg


def test_load_hybrid_history_selection_metric_includes_avg_score(caplog):
    """Selection metric includes avg_score of selected messages."""
    pool = [
        _make_message("pro plan pricing is $49", rank_hint=0),
        _make_message("unrelated weather", rank_hint=1),
        _make_message("another pro plan detail", rank_hint=2),
    ]
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = pool

    incoming_msg = _make_message("what is the pro plan price?")
    incoming_msg.sender_id = "s"
    incoming_msg.channel = "gmail"
    incoming_msg.user_id = "u"
    incoming_msg.id = "in"

    with caplog.at_level("INFO"):
        TwinEngineService._load_hybrid_history(mock_db, incoming_msg, "u")

    metric_recs = [rec for rec in caplog.records if "hybrid_history_selection" in rec.message and "avg_score" in rec.message]
    assert metric_recs, "Expected selection metric log containing avg_score"
