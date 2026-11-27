"""Unit test for average age in hybrid history selection metric (ADR-002)."""
from __future__ import annotations

from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock, patch

from app.services.twin_engine import TwinEngineService
from app.models.message import Message


def _make_message(content: str, age_days: float = 0.0, rank_hint: int = 0) -> Message:
    msg = MagicMock(spec=Message)
    msg.content = content
    msg.id = f"msg-{rank_hint}"
    msg.created_at = datetime.now(UTC) - timedelta(days=age_days)
    msg.channel = "gmail"
    msg.sender_name = "Alice"
    return msg


def test_load_hybrid_history_includes_avg_age_days(caplog):
    """Selection metric includes avg_age_days of selected messages."""
    pool = [
        _make_message("pro plan pricing is $49", age_days=1.0, rank_hint=0),
        _make_message("unrelated weather talk", age_days=5.0, rank_hint=1),
        _make_message("another pro plan detail about features", age_days=2.0, rank_hint=2),
    ]
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = pool

    incoming_msg = _make_message("what is the pro plan price?", age_days=0)
    incoming_msg.sender_id = "s"
    incoming_msg.channel = "gmail"
    incoming_msg.user_id = "u"
    incoming_msg.id = "in"

    with patch("app.services.twin_engine.settings") as mock_settings:
        mock_settings.hybrid_history_pool_size = 20
        mock_settings.hybrid_history_top_k = 5
        mock_settings.hybrid_history_min_score = 0.0
        mock_settings.hybrid_history_diversity_threshold = 0.0
        mock_settings.hybrid_history_cross_channel = False
        mock_settings.hybrid_history_use_time_based_recency = False
        mock_settings.hybrid_history_recency_weight = 0.7
        mock_settings.hybrid_history_overlap_weight = 0.3
        mock_settings.hybrid_history_recency_half_life_days = 7.0

        with caplog.at_level("INFO"):
            TwinEngineService._load_hybrid_history(mock_db, incoming_msg, "u")

    sel_recs = [rec for rec in caplog.records if "hybrid_history_selection" in rec.message]
    assert sel_recs, "Expected selection metric log"
    assert any(getattr(rec, "avg_age_days", 0) > 0 for rec in sel_recs)
    assert any("avg_age_days=" in rec.message for rec in sel_recs)
