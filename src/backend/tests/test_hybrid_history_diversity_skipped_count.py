"""Unit test for diversity_skipped_count in hybrid_history_selection metric."""
from __future__ import annotations

from datetime import datetime, UTC
from unittest.mock import MagicMock, patch

import pytest

from app.services.twin_engine import TwinEngineService
from app.models.message import Message


def _make_message(content: str, rank_hint: int = 0) -> Message:
    msg = MagicMock(spec=Message)
    msg.content = content
    msg.id = f"msg-{rank_hint}"
    msg.created_at = datetime.now(UTC)
    msg.sender_id = "s"
    msg.channel = "gmail"
    msg.user_id = "u"
    return msg


def test_load_hybrid_history_includes_diversity_skipped_count(caplog):
    """Selection metric includes diversity_skipped_count when diversity filter skips messages."""
    pool = [
        _make_message("The pro plan costs $49 per month with annual billing and includes support.", 0),
        _make_message("Pro plan pricing is $49 monthly including annual billing and support options.", 1),
        _make_message("Enterprise plans start at custom pricing. Contact sales for details.", 2),
    ]
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = pool

    incoming_msg = _make_message("What is the pro plan price?")
    incoming_msg.id = "incoming"

    with patch("app.services.twin_engine.settings") as mock_settings:
        mock_settings.hybrid_history_pool_size = 20
        mock_settings.hybrid_history_top_k = 3
        mock_settings.hybrid_history_min_score = 0.0
        mock_settings.hybrid_history_diversity_threshold = 0.6
        mock_settings.hybrid_history_cross_channel = False
        mock_settings.hybrid_history_use_time_based_recency = False
        mock_settings.hybrid_history_recency_half_life_days = 7.0
        mock_settings.hybrid_history_recency_weight = 0.7
        mock_settings.hybrid_history_overlap_weight = 0.3

        with caplog.at_level("INFO"):
            TwinEngineService._load_hybrid_history(mock_db, incoming_msg, "u")

    metric_recs = [rec for rec in caplog.records if "hybrid_history_selection" in rec.message and "diversity_skipped" in rec.message]
    assert metric_recs, "Expected selection metric with diversity_skipped field"
    # Verify the extra payload has the field (if logging extra is captured; at minimum the message contains it)
    assert any("diversity_skipped" in rec.message for rec in metric_recs)
