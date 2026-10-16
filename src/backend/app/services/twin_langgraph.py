"""
LangGraph Twin Engine Graph (Phase 2+)

Wraps the existing TwinEngineService sequential pipeline as an interruptible
StateGraph. Enables human-in-the-loop (HITL) via interrupt_before on the
await_human node, matching the architecture in docs/05-technical/SELPH_System-Architecture.md.

Usage:
    from app.services.twin_langgraph import build_twin_graph, TwinEngineState
    graph = build_twin_graph()
    # config = {"configurable": {"thread_id": message_id}}
    # result = graph.invoke({"message_id": mid, "user_id": uid, "db": db}, config)
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

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


def load_context_node(state: TwinEngineState) -> TwinEngineState:
    """Load twin context, identity, topics, briefings, and history."""
    db = state["db"]
    message = db.query(__import__("app.models", fromlist=["Message"]).Message).filter(
        __import__("app.models", fromlist=["Message"]).Message.id == state["message_id"],
        __import__("app.models", fromlist=["Message"]).Message.user_id == state["user_id"],
    ).first()
    if not message:
        return {"error": "Message not found"}
    ctx = TwinEngineService._load_context(db, message, state["user_id"])
    system_prompt, user_prompt = TwinEngineService._build_prompts(ctx)
    return {"ctx": ctx, "system_prompt": system_prompt, "user_prompt": user_prompt}


def generate_draft_node(state: TwinEngineState) -> TwinEngineState:
    """Generate draft via LLM or deterministic fallback."""
    if state.get("error"):
        return state
    ctx = state["ctx"]
    draft, factors, reasoning, flags, source, metrics = TwinEngineService._generate_draft(
        ctx, state["system_prompt"], state["user_prompt"]
    )
    return {
        "draft": draft,
        "factors": factors,
        "generator_reasoning": reasoning,
        "generator_flags": flags,
        "generation_source": source,
        "generation_metrics": metrics,
    }


def score_and_moderate_node(state: TwinEngineState) -> TwinEngineState:
    """Compute confidence and run content safety moderation."""
    if state.get("error"):
        return state
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


def await_human_node(state: TwinEngineState) -> TwinEngineState:
    """Interrupt point for human approval. No-op; graph pauses before this node."""
    logger.info("HITL interrupt: awaiting human decision for message_id=%s", state.get("message_id"))
    return state


def process_decision_node(state: TwinEngineState) -> TwinEngineState:
    """Post-HITL processing (placeholder for approve/edit/reject side-effects)."""
    # In full integration this would call DraftService based on human decision stored in state.
    result = {
        "draft": state.get("draft"),
        "confidence_score": state.get("confidence_score"),
        "confidence_label": state.get("confidence_label"),
        "moderation_passed": state.get("moderation_passed"),
        "reasoning": state.get("reasoning"),
        "generation_source": state.get("generation_source"),
    }
    return {"result": result}


def build_twin_graph() -> Any:
    """Compile the Twin Engine StateGraph with HITL interrupt."""
    workflow = StateGraph(TwinEngineState)

    workflow.add_node("load_context", load_context_node)
    workflow.add_node("generate_draft", generate_draft_node)
    workflow.add_node("score_and_moderate", score_and_moderate_node)
    workflow.add_node("await_human", await_human_node)
    workflow.add_node("process_decision", process_decision_node)

    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "generate_draft")
    workflow.add_edge("generate_draft", "score_and_moderate")
    workflow.add_edge("score_and_moderate", "await_human")
    workflow.add_edge("await_human", "process_decision")
    workflow.add_edge("process_decision", END)

    # Interrupt before human node so the graph can be resumed after approval.
    # Checkpointer (PostgresSaver / RedisSaver) should be supplied at compile time in production.
    graph = workflow.compile(interrupt_before=["await_human"])
    return graph


# Convenience re-export
__all__ = ["build_twin_graph", "TwinEngineState"]
