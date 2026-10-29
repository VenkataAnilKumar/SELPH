"""Unit tests for TwinEngineGraph routing and core nodes."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from app.services.twin_langgraph import (
    route_after_moderation,
    flag_for_review_node,
    process_decision_node,
    await_human_node,
    audit_log_node,
    _persist_audit,
    _classify_error,
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


def test_audit_log_node_flagged_path():
    state = {
        "message_id": "msg-audit-1",
        "user_id": "user-1",
        "flagged_for_review": True,
        "moderation_passed": False,
        "moderation_flags": ["spam"],
        "risk_score": 0.9,
        "confidence_score": 0.1,
        "confidence_label": "low",
        "result": {"status": "flagged", "recommended_action": "manual_review"},
    }
    out = audit_log_node(state)
    assert "audit_event" in out
    audit = out["audit_event"]
    assert audit["event_type"] == "flagged_for_review"
    assert audit["message_id"] == "msg-audit-1"
    assert audit["moderation_flags"] == ["spam"]
    assert audit["confidence_label"] == "low"
    assert audit["hitl_priority"] == "high"
    assert audit["risk_band"] == "high"
    assert audit["moderation_flag_count"] == 1
    assert "context_signals" in audit
    assert out["result"]["audit"]["event_type"] == "flagged_for_review"


def test_audit_log_node_hitl_path():
    state = {
        "message_id": "msg-audit-2",
        "user_id": "user-2",
        "flagged_for_review": False,
        "moderation_passed": True,
        "moderation_flags": [],
        "risk_score": 0.1,
        "confidence_score": 0.9,
        "confidence_label": "high",
        "result": {"status": "ready_for_decision", "recommended_action": "await_human_approval"},
    }
    out = audit_log_node(state)
    audit = out["audit_event"]
    assert audit["event_type"] == "ready_for_hitl"
    assert audit["moderation_passed"] is True
    assert audit["confidence_label"] == "high"
    assert audit["hitl_priority"] == "normal"
    assert audit["risk_band"] == "low"
    assert audit["moderation_flag_count"] == 0
    assert "context_signals" in audit
    assert "audit" in out["result"]


def test_audit_log_node_includes_error():
    """Error paths still produce a complete audit event with the error field."""
    state = {
        "message_id": "msg-err",
        "user_id": "user-err",
        "flagged_for_review": True,
        "error": "Message not found",
        "result": {"status": "flagged", "recommended_action": "manual_review"},
    }
    out = audit_log_node(state)
    audit = out["audit_event"]
    assert audit["error"] == "Message not found"
    assert audit["event_type"] == "flagged_for_review"
    assert audit["error_category"] == "not_found"
    assert "context_signals" in audit
    assert out["result"]["audit"]["error"] == "Message not found"


def test_audit_log_node_persists_when_db_present():
    """When a DB session is available, audit is persisted (best-effort)."""
    mock_db = MagicMock()
    state = {
        "message_id": "msg-persist",
        "user_id": "user-persist",
        "db": mock_db,
        "flagged_for_review": False,
        "moderation_passed": True,
        "result": {"status": "ready_for_decision"},
    }
    with patch("app.services.twin_langgraph.AuditLog") as MockAuditLog:
        out = audit_log_node(state)
        assert "audit_event" in out
        # Persistence attempted
        mock_db.add.assert_called()
        mock_db.flush.assert_called()


def test_persist_audit_handles_failure_gracefully():
    """Persistence errors must not propagate."""
    mock_db = MagicMock()
    mock_db.add.side_effect = RuntimeError("db down")
    audit = {"message_id": "msg-fail", "event_type": "ready_for_hitl"}
    # Should not raise
    _persist_audit(mock_db, audit, "user-1")


def test_audit_log_node_includes_graph_duration():
    """Audit event includes graph_duration_ms when start timestamp is present."""
    start = time.perf_counter_ns()
    state = {
        "message_id": "msg-dur",
        "user_id": "user-dur",
        "flagged_for_review": False,
        "graph_start_ns": start,
        "result": {"status": "ready_for_decision"},
    }
    out = audit_log_node(state)
    audit = out["audit_event"]
    assert "graph_duration_ms" in audit
    assert isinstance(audit["graph_duration_ms"], int)
    assert audit["graph_duration_ms"] >= 0


def test_classify_error_categories():
    """Error classifier covers common TwinEngine failure modes."""
    assert _classify_error("Message not found") == "not_found"
    assert _classify_error("generation failed after retry") == "generation"
    assert _classify_error("moderation service error") == "moderation"
    assert _classify_error("request timed out") == "timeout"
    assert _classify_error("unexpected boom") == "unknown"
    assert _classify_error(None) is None


def test_audit_log_node_includes_context_signals():
    """Audit event includes lightweight context_signals for grounding observability."""
    mock_ctx = MagicMock()
    mock_ctx.briefing = "Keep it short this week"
    state = {
        "message_id": "msg-ctx",
        "user_id": "user-ctx",
        "flagged_for_review": False,
        "factors": {"topic_known": True, "no_avoided_topics": True},
        "generation_source": "llm",
        "ctx": mock_ctx,
        "result": {"status": "ready_for_decision"},
    }
    out = audit_log_node(state)
    audit = out["audit_event"]
    signals = audit.get("context_signals") or {}
    assert signals.get("topic_known") is True
    assert signals.get("no_avoided_topics") is True
    assert signals.get("generation_source") == "llm"
    assert signals.get("has_briefing") is True


def test_audit_log_node_includes_risk_band_and_flag_count():
    """Audit event includes risk_band and moderation_flag_count for triage."""
    state = {
        "message_id": "msg-risk",
        "user_id": "user-risk",
        "flagged_for_review": True,
        "moderation_flags": ["spam", "phishing"],
        "risk_score": 0.5,
        "result": {"status": "flagged"},
    }
    out = audit_log_node(state)
    audit = out["audit_event"]
    assert audit["risk_band"] == "medium"
    assert audit["moderation_flag_count"] == 2
