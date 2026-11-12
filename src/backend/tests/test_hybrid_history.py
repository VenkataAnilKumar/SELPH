"""Unit tests for hybrid short-term memory retrieval (ADR-002)."""
from __future__ import annotations

from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.twin_engine import TwinEngineService
from app.models.message import Message


def _make_message(content: str, rank_hint: int = 0, created_at: datetime | None = None) -> Message:
    """Create a lightweight Message-like object for scoring tests."""
    msg = MagicMock(spec=Message)
    msg.content = content
    msg.id = f"msg-{rank_hint}"
    msg.created_at = created_at or datetime.now(UTC)
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


def test_load_hybrid_history_respects_configurable_pool_size(monkeypatch):
    """Candidate pool size comes from settings.hybrid_history_pool_size."""
    pool = [_make_message(f"msg {i}") for i in range(30)]
    mock_db = MagicMock()
    # Capture the limit that was requested
    captured_limit = []

    def fake_limit(n):
        captured_limit.append(n)
        m = MagicMock()
        m.all.return_value = pool[:n]
        return m

    mock_db.query.return_value.filter.return_value.order_by.return_value.limit = fake_limit

    incoming_msg = _make_message("test")
    incoming_msg.sender_id = "s"
    incoming_msg.channel = "c"
    incoming_msg.user_id = "u"
    incoming_msg.id = "in"

    # Temporarily override the setting
    from app.config import settings
    original = settings.hybrid_history_pool_size
    try:
        settings.hybrid_history_pool_size = 15
        TwinEngineService._load_hybrid_history(mock_db, incoming_msg, "u")
        assert captured_limit and captured_limit[0] == 15
    finally:
        settings.hybrid_history_pool_size = original


def test_load_hybrid_history_respects_configurable_top_k(monkeypatch):
    """Top-K selection comes from settings.hybrid_history_top_k."""
    pool = []
    for i in range(15):
        content = f"filler {i}"
        if i == 10:
            content = "relevant pro plan pricing details here"
        pool.append(_make_message(content, rank_hint=i))

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = pool

    incoming_msg = _make_message("pro plan pricing")
    incoming_msg.sender_id = "s"
    incoming_msg.channel = "c"
    incoming_msg.user_id = "u"
    incoming_msg.id = "in"

    from app.config import settings
    original = settings.hybrid_history_top_k
    try:
        settings.hybrid_history_top_k = 3
        result = TwinEngineService._load_hybrid_history(mock_db, incoming_msg, "u")
        assert len(result) == 3
        # Relevant message should still be included
        contents = [m.content for m in result]
        assert any("pro plan" in c for c in contents)
    finally:
        settings.hybrid_history_top_k = original


def test_score_history_message_respects_configurable_weights():
    """Scoring weights come from settings and affect ranking."""
    incoming = "What is the price of the pro plan?"
    recent_irrelevant = _make_message("How is the weather today?", rank_hint=0)
    older_relevant = _make_message("The pro plan costs $49 per month with annual billing.", rank_hint=5)

    from app.config import settings
    original_r = settings.hybrid_history_recency_weight
    original_o = settings.hybrid_history_overlap_weight
    try:
        # Extreme overlap preference should make older relevant win more clearly
        settings.hybrid_history_recency_weight = 0.2
        settings.hybrid_history_overlap_weight = 0.8
        score_recent = TwinEngineService._score_history_message(recent_irrelevant, incoming, rank=0, pool_size=10)
        score_older = TwinEngineService._score_history_message(older_relevant, incoming, rank=5, pool_size=10)
        assert score_older > score_recent

        # Extreme recency preference should reverse or narrow the gap
        settings.hybrid_history_recency_weight = 0.95
        settings.hybrid_history_overlap_weight = 0.05
        score_recent_high_r = TwinEngineService._score_history_message(recent_irrelevant, incoming, rank=0, pool_size=10)
        score_older_high_r = TwinEngineService._score_history_message(older_relevant, incoming, rank=5, pool_size=10)
        assert score_recent_high_r > score_older_high_r or abs(score_recent_high_r - score_older_high_r) < 0.15
    finally:
        settings.hybrid_history_recency_weight = original_r
        settings.hybrid_history_overlap_weight = original_o


def test_score_history_message_time_based_recency_prefers_recent():
    """When time-based recency is enabled, a very recent message scores higher on pure recency than an old one."""
    incoming = "hello uniquephrase"
    now = datetime.now(UTC)
    recent = _make_message("unrelated", created_at=now - timedelta(hours=1))
    old = _make_message("also unrelated", created_at=now - timedelta(days=14))

    from app.config import settings
    original_flag = settings.hybrid_history_use_time_based_recency
    original_half = settings.hybrid_history_recency_half_life_days
    try:
        settings.hybrid_history_use_time_based_recency = True
        settings.hybrid_history_recency_half_life_days = 7.0
        score_recent = TwinEngineService._score_history_message(recent, incoming, rank=0, pool_size=10)
        score_old = TwinEngineService._score_history_message(old, incoming, rank=5, pool_size=10)
        assert score_recent > score_old
    finally:
        settings.hybrid_history_use_time_based_recency = original_flag
        settings.hybrid_history_recency_half_life_days = original_half


def test_format_relative_time_human_friendly():
    """Relative time formatter produces expected human-readable strings."""
    now = datetime.now(UTC)
    assert TwinEngineService._format_relative_time(now - timedelta(seconds=30)) == "just now"
    assert TwinEngineService._format_relative_time(now - timedelta(minutes=5)) == "5m ago"
    assert TwinEngineService._format_relative_time(now - timedelta(hours=3)) == "3h ago"
    assert TwinEngineService._format_relative_time(now - timedelta(days=1)) == "yesterday"
    assert TwinEngineService._format_relative_time(now - timedelta(days=3)) == "3d ago"
    assert TwinEngineService._format_relative_time(now - timedelta(days=8)) == "last week"
    assert TwinEngineService._format_relative_time(None) == "unknown time"


def test_build_history_prompt_includes_relative_times():
    """History prompt includes the relative time prefix."""
    msgs = [
        _make_message("What is the price?", created_at=datetime.now(UTC) - timedelta(hours=2)),
        _make_message("Thanks for the info.", created_at=datetime.now(UTC) - timedelta(days=1)),
    ]
    prompt = TwinEngineService._build_history_prompt(msgs)
    assert "[2h ago]" in prompt or "[1h ago]" in prompt or "[3h ago]" in prompt  # approximate
    assert "yesterday" in prompt
    assert "Recent conversation history" in prompt
