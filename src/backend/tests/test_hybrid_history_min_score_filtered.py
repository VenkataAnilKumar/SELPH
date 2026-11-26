"""Unit test for min-score filtered metric in hybrid history (ADR-002)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.twin_engine import TwinEngineService
from app.models.message import Message


def _make_message(content: str, rank_hint: int = 0) -> Message:
    msg = MagicMock(spec=Message)
    msg.content = content
    msg.id = f"msg-{rank_hint}"
    msg.created_at = None
    return msg


def test_load_hybrid_history_emits_min_score_filtered_metric(caplog):
    """When messages are filtered by min_score, emit hybrid_history_min_score_filtered."""
    pool = [
        _make_message("pro plan pricing is $49", rank_hint=0),
        _make_message("unrelated weather talk", rank_hint=1),
        _make_message("another pro plan detail about features", rank_hint=2),
    ]
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = pool

    incoming_msg = _make_message("what is the pro plan price?")
    incoming_msg.sender_id = "s"
    incoming_msg.channel = "gmail"
    incoming_msg.user_id = "u"
    incoming_msg.id = "in"

    with patch("app.services.twin_engine.settings") as mock_settings:
        mock_settings.hybrid_history_pool_size = 20
        mock_settings.hybrid_history_top_k = 5
        mock_settings.hybrid_history_min_score = 0.5  # force some filtering
        mock_settings.hybrid_history_diversity_threshold = 0.0
        mock_settings.hybrid_history_cross_channel = False
        mock_settings.hybrid_history_use_time_based_recency = False
        mock_settings.hybrid_history_recency_weight = 0.7
        mock_settings.hybrid_history_overlap_weight = 0.3
        mock_settings.hybrid_history_recency_half_life_days = 7.0

        with caplog.at_level("INFO"):
            TwinEngineService._load_hybrid_history(mock_db, incoming_msg, "u")

    filtered_recs = [rec for rec in caplog.records if "hybrid_history_min_score_filtered" in rec.message]
    assert filtered_recs, "Expected min_score_filtered metric log"
    assert any(getattr(rec, "filtered_count", 0) > 0 for rec in filtered_recs)
