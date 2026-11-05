"""Unit tests for hybrid short-term memory retrieval (ADR-002)."""
from __future__ import annotations

from datetime import datetime, UTC
from unittest.mock import MagicMock, patch

import pytest

from app.services.twin_engine import TwinEngineService
from app.models.message import Message


def _make_message(content: str, rank_hint: int = 0) -> Message:
    """Create a lightweight Message-like object for scoring tests."""
    msg = MagicMock(spec=Message)
    msg.content = content
    msg.id = f"msg-{rank_hint}"
    msg.created_at = datetime.now(UTC)
    return msg


def test_score_history_message_prefers_relevant_over_recent_irrelevant():
    """A relevant older message should outscore a recent irrelevant one."""
    incoming = "What is the price of the pro plan?"
    # Rank 0 = most recent
    recent_irrelevant = _make_message("How is the weather today?", rank_hint=0)
    older_relevant = _make_message("The pro plan costs $49 per month with annual billing.", rank_hint=5)

    # Pool size 10 for decay calculation
    score_recent = TwinEngineService._score_history_message(recent_irrelevant, incoming, rank=0, pool_size=10)
    score_older = TwinEngineService._score_history_message(older_relevant, incoming, rank=5, pool_size=10)

    # Older relevant should score higher due to token overlap dominating the mild recency decay
    assert score_older > score_recent
    assert score_older > 0.4  # has meaningful overlap


def test_score_history_message_pure_recency_when_no_overlap():
    """When no token overlap, ranking is pure recency."""
    incoming = "hello world uniquephrase"
    msg0 = _make_message("unrelated content here", rank_hint=0)
    msg5 = _make_message("also unrelated stuff", rank_hint=5)

    s0 = TwinEngineService._score_history_message(msg0, incoming, rank=0, pool_size=10)
    s5 = TwinEngineService._score_history_message(msg5, incoming, rank=5, pool_size=10)
    assert s0 > s5


def test_score_history_message_stopwords_do_not_inflate_overlap():
    """Common stopwords should not create artificial token overlap."""
    incoming = "What is the price of the pro plan?"
    # Message that only shares stopwords / generic words
    stopword_heavy = _make_message("This is what they have been doing with their time.", rank_hint=1)
    score = TwinEngineService._score_history_message(stopword_heavy, incoming, rank=1, pool_size=10)
    # Overlap should be near zero after stopword filtering
    assert score < 0.75  # recency dominates; no meaningful content overlap


def test_load_hybrid_history_selects_top_scored():
    """_load_hybrid_history returns top-5 by hybrid score from the candidate pool."""
    # Create a pool of 10 messages (simpler than 20)
    pool = []
    for i in range(10):
        content = "irrelevant filler message number " + str(i)
        if i == 7:
            content = "The pricing for enterprise is custom. Contact sales for pro plan details."
        pool.append(_make_message(content, rank_hint=i))

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = pool

    incoming_msg = _make_message("Tell me about the pro plan pricing", rank_hint=-1)
    incoming_msg.sender_id = "sender-1"
    incoming_msg.channel = "gmail"
    incoming_msg.user_id = "user-1"
    incoming_msg.id = "incoming"

    result = TwinEngineService._load_hybrid_history(mock_db, incoming_msg, "user-1")

    assert len(result) == 5
    # The relevant one (index 7 in original pool) should be among the top
    contents = [m.content for m in result]
    assert any("pro plan" in c or "pricing" in c for c in contents)
