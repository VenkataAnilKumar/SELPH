"""Unit tests for TwinEngineGraph routing and core nodes."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.twin_langgraph import (
    route_after_moderation,
    flag_for_review_node,
    process_decision_node,
    await_human_node,
)


def test_route_after_moderation_safe():
    state = {"moderation_passed": True}
    assert route_after_moderation(state) == "await_human"


def test_route_after_moderation_flagged():
    state = {"moderation_passed": False, "moderation_flags": ["spam"]}
    assert route_after_moderation(state) == "flag_for_review"


def test_route_after_moderation_error():
    state = {"error": "boom", "moderation_passed": True}
    assert route_after_moderation(state) == "flag_for_review"


def test_flag_for_review_node_enriches_result():
    state = {
        "message_id": "msg-123",
        "draft": "hello",
        "moderation_flags": ["unsafe"],
        "risk_score": 0.8,
        "confidence_score": 0.2,
    }
    out = flag_for_review_node(state)
    assert out["flagged_for_review"] is True
    result = out["result"]
    assert result["status"] == "flagged"
    assert result["recommended_action"] == "manual_review"
    assert result["message_id"] == "msg-123"
    assert "timestamp" in result
    assert result["moderation_flags"] == ["unsafe"]


def test_process_decision_node_enriches_result():
    state = {
        "message_id": "msg-456",
        "draft": "approved draft",
        "confidence_score": 0.85,
        "confidence_label": "high",
        "moderation_passed": True,
        "moderation_flags": [],
        "reasoning": "ok",
        "generation_source": "llm",
    }
    out = process_decision_node(state)
    result = out["result"]
    assert result["status"] == "ready_for_decision"
    assert result["recommended_action"] == "await_human_approval"
    assert result["message_id"] == "msg-456"
    assert "timestamp" in result
    assert result["moderation_passed"] is True


def test_await_human_node_noop():
    state = {"message_id": "msg-789"}
    out = await_human_node(state)
    assert out is state or out == state
