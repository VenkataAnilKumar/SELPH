"""
LangGraph Twin Engine Graph (Phase 2+)

Wraps the existing TwinEngineService sequential pipeline as an interruptible
StateGraph. Enables human-in-the-loop (HITL) via interrupt_before on the
await_human node, matching the architecture in docs/05-technical/SELPH_System-Architecture.md.

Enhancements:
- Conditional routing based on moderation_passed (flag_for_review vs await_human)
- Explicit flag_for_review node for safety-flagged drafts
- Dedicated audit_log_node for structured observability on both paths
- Optional durable persistence of audit events to the AuditLog table
- Better error handling, structured logging, and enriched result payloads for HITL/audit
- Audit events now capture generation_source, selective metrics, channel, and graph duration for end-to-end observability
- generate_draft_node retries once on transient failure before erroring

Usage:
    from app.services.twin_langgraph import build_twin_graph, TwinEngineState
    graph = build_twin_graph()
    # config = {"configurable": {"thread_id": message_id}}
    # result = graph.invoke({"message_id": mid, "user_id": uid, "db": db}, config)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Literal, TypedDict

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.services.twin_engine import TwinEngineService
from app.services.moderation import ModerationService

logger = logging.getLogger(__name__)


class TwinEngineState(TypedDict, total=False):
    """State flowing through the Twin Engine graph."""
    message_id: str
    user_id: str
    db: Session
    ctx: Any
    system_prompt: str
    user_prompt: str
    draft: str
    factors: dict
    generator_reasoning: str
    generator_flags: list
    generation_source: str
    generation_metrics: dict
    confidence_score: float
    confidence_label: str
    moderation_passed: bool
    moderation_flags: list
    risk_score: float
    reasoning: str
    result: dict
    error: str | None
    flagged_for_review: bool
    audit_event: dict
    graph_start_ns: int


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_context_node(state: TwinEngineState) -> TwinEngineState:
    """Load twin context, identity, topics, briefings, and history."""
    try:
        db = state["db"]
        Message = __import__("app.models", fromlist=["Message"]).Message
        message = db.query(Message).filter(
            Message.id == state["message_id"],
            Message.user_id == state["user_id"],
        ).first()
        if not message:
            return {"error": "Message not found", "graph_start_ns": time.perf_counter_ns()}
        ctx = TwinEngineService._load_context(db, message, state["user_id"])
        system_prompt, user_prompt = TwinEngineService._build_prompts(ctx)
        return {
            "ctx": ctx,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "graph_start_ns": time.perf_counter_ns(),
        }
    except Exception as exc:
        logger.exception("load_context_node failed for message_id=%s", state.get("message_id"))
        return {"error": str(exc), "graph_start_ns": time.perf_counter_ns()}


def generate_draft_node(state: TwinEngineState) -> TwinEngineState:
    """Generate draft via LLM or deterministic fallback. Retries once on transient failure."""
    if state.get("error"):
        return state
    last_exc: Exception | None = None
    for attempt in range(2):  # initial + one retry
        try:
            ctx = state["ctx"]
            draft, factors, reasoning, flags, source, metrics = TwinEngineService._generate_draft(
                ctx, state["system_prompt"], state["user_prompt"]
            )
            if attempt > 0:
                logger.info("generate_draft_node succeeded on retry for message_id=%s", state.get("message_id"))
            return {
                "draft": draft,
                "factors": factors,
                "generator_reasoning": reasoning,
                "generator_flags": flags,
                "generation_source": source,
                "generation_metrics": metrics,
            }
        except Exception as exc:
            last_exc = exc
            logger.warning("generate_draft_node attempt %d failed: %s", attempt + 1, exc)
            if attempt == 0:
                continue  # retry once
    logger.exception("generate_draft_node failed after retry")
    return {"error": str(last_exc) if last_exc else "generation failed"}


def score_and_moderate_node(state: TwinEngineState) -> TwinEngineState:
    """Compute confidence and run content safety moderation."""
    if state.get("error"):
        return state
    try:
        factors = state["factors"]
        confidence_score = TwinEngineService._compute_overall_confidence(factors)
        confidence_label = ModerationService.get_confidence_label(confidence_score)
        moderation_passed, flags, risk_score = ModerationService.check_content_safety(state["draft"])
        if not moderation_passed:
            confidence_score = min(confidence_score, 0.3)
            confidence_label = ModerationService.get_confidence_label(confidence_score)
        reasoning = (
            f"{state['generator_reasoning']} Generated with channel='{state['ctx'].message.channel}', "
            f"topic_known={factors['topic_known']}, no_avoided_topics={factors['no_avoided_topics']}, "
            f"moderation_risk={risk_score}."
        )
        return {
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
            "moderation_passed": moderation_passed,
            "moderation_flags": flags,
            "risk_score": risk_score,
            "reasoning": reasoning,
        }
    except Exception as exc:
        logger.exception("score_and_moderate_node failed")
        return {"error": str(exc)}


def route_after_moderation(state: TwinEngineState) -> Literal["await_human", "flag_for_review"]:
    """Conditional router: HITL if safe, else flag for manual review."""
    if state.get("error") or not state.get("moderation_passed", False):
        return "flag_for_review"
    return "await_human"


def await_human_node(state: TwinEngineState) -> TwinEngineState:
    """Interrupt point for human approval. No-op; graph pauses before this node."""
    logger.info("HITL interrupt: awaiting human decision for message_id=%s", state.get("message_id"))
    return state


def flag_for_review_node(state: TwinEngineState) -> TwinEngineState:
    """Mark draft as flagged for manual safety review; no automatic HITL."""
    msg_id = state.get("message_id")
    flags = state.get("moderation_flags") or []
    risk = state.get("risk_score")
    logger.warning(
        "Draft flagged for review message_id=%s flags=%s risk=%s",
        msg_id,
        flags,
        risk,
    )
    result = {
        "status": "flagged",
        "draft": state.get("draft"),
        "moderation_flags": flags,
        "risk_score": risk,
        "confidence_score": state.get("confidence_score"),
        "recommended_action": "manual_review",
        "timestamp": _now_iso(),
        "message_id": msg_id,
    }
    return {"flagged_for_review": True, "result": result}


def process_decision_node(state: TwinEngineState) -> TwinEngineState:
    """Post-HITL processing (placeholder for approve/edit/reject side-effects)."""
    result = {
        "draft": state.get("draft"),
        "confidence_score": state.get("confidence_score"),
        "confidence_label": state.get("confidence_label"),
        "moderation_passed": state.get("moderation_passed"),
        "moderation_flags": state.get("moderation_flags") or [],
        "reasoning": state.get("reasoning"),
        "generation_source": state.get("generation_source"),
        "status": "ready_for_decision",
        "recommended_action": "await_human_approval",
        "timestamp": _now_iso(),
        "message_id": state.get("message_id"),
    }
    logger.info(
        "Draft ready for HITL message_id=%s confidence=%s moderation_passed=%s",
        state.get("message_id"),
        state.get("confidence_score"),
        state.get("moderation_passed"),
    )
    return {"result": result}


def _persist_audit(db: Session | None, audit: dict, user_id: str | None) -> None:
    """Best-effort durable write of the audit event. Never raises."""
    if db is None or not user_id:
        return
    try:
        from app.models import AuditLog
        log = AuditLog(
            user_id=user_id,
            action="twin_engine_audit",
            resource_type="Message",
            resource_id=audit.get("message_id"),
            details=audit,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log)
        db.flush()  # or commit if the caller expects it; flush keeps transaction control with caller
        logger.debug("Persisted TwinEngine audit for message_id=%s", audit.get("message_id"))
    except Exception as exc:
        logger.warning("Failed to persist TwinEngine audit event: %s", exc)


def audit_log_node(state: TwinEngineState) -> TwinEngineState:
    """Standardize and log an audit event for both HITL and flagged paths. Improves observability."""
    result = state.get("result") or {}
    event_type = "flagged_for_review" if state.get("flagged_for_review") else "ready_for_hitl"
    # Prefer explicit error if present (even on non-flagged paths)
    error_msg = state.get("error")
    # Selective metrics for observability without bloating the audit payload
    metrics = state.get("generation_metrics") or {}
    selective_metrics = {
        k: metrics[k]
        for k in ("llm_latency_ms", "parse_retry_count", "llm_calls", "fallback_reason")
        if k in metrics
    }
    # Optional channel for better traceability (from context when available)
    channel = None
    try:
        ctx = state.get("ctx")
        if ctx and hasattr(ctx, "message") and hasattr(ctx.message, "channel"):
            channel = ctx.message.channel
    except Exception:
        pass
    # Graph duration for end-to-end latency observability
    graph_duration_ms: int | None = None
    start_ns = state.get("graph_start_ns")
    if isinstance(start_ns, int):
        graph_duration_ms = int((time.perf_counter_ns() - start_ns) / 1_000_000)
    audit = {
        "event_type": event_type,
        "message_id": state.get("message_id"),
        "user_id": state.get("user_id"),
        "status": result.get("status"),
        "recommended_action": result.get("recommended_action"),
        "moderation_passed": state.get("moderation_passed"),
        "moderation_flags": state.get("moderation_flags") or [],
        "risk_score": state.get("risk_score"),
        "confidence_score": state.get("confidence_score"),
        "generation_source": state.get("generation_source"),
        "generation_metrics": selective_metrics or None,
        "channel": channel,
        "graph_duration_ms": graph_duration_ms,
        "timestamp": _now_iso(),
        "error": error_msg,
    }
    logger.info("TwinEngine audit event: %s", audit)
    # Attach to result for callers / checkpointer consumers
    result = {**result, "audit": audit}
    # Best-effort durable persistence (non-blocking)
    _persist_audit(state.get("db"), audit, state.get("user_id"))
    return {"result": result, "audit_event": audit}


def build_twin_graph() -> Any:
    """Compile the Twin Engine StateGraph with HITL interrupt, conditional safety routing, and audit logging."""
    workflow = StateGraph(TwinEngineState)

    workflow.add_node("load_context", load_context_node)
    workflow.add_node("generate_draft", generate_draft_node)
    workflow.add_node("score_and_moderate", score_and_moderate_node)
    workflow.add_node("await_human", await_human_node)
    workflow.add_node("flag_for_review", flag_for_review_node)
    workflow.add_node("process_decision", process_decision_node)
    workflow.add_node("audit_log", audit_log_node)

    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "generate_draft")
    workflow.add_edge("generate_draft", "score_and_moderate")
    workflow.add_conditional_edges(
        "score_and_moderate",
        route_after_moderation,
        {
            "await_human": "await_human",
            "flag_for_review": "flag_for_review",
        },
    )
    workflow.add_edge("await_human", "process_decision")
    workflow.add_edge("process_decision", "audit_log")
    workflow.add_edge("flag_for_review", "audit_log")
    workflow.add_edge("audit_log", END)

    # Interrupt before human node so the graph can be resumed after approval.
    # Checkpointer (PostgresSaver / RedisSaver) should be supplied at compile time in production.
    graph = workflow.compile(interrupt_before=["await_human"])
    return graph


# Convenience re-export
__all__ = ["build_twin_graph", "TwinEngineState"]
