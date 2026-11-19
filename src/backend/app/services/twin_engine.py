"""Twin Engine — context loading, hybrid short-term memory, and prompt construction.

Implements ADR-002: pure recency (limit=5) by default; hybrid scoring behind
FEATURE_HYBRID_HISTORY. History prompts include relative timestamps.
Pool size, top-K, scoring weights, optional time-based recency, min score,
optional prompt char limit, optional diversity threshold, and optional cross-channel are configurable.
Emits structured hybrid_history_selection, hybrid_history_prompt_truncated,
hybrid_history_fallback, hybrid_history_diversity_skipped, and hybrid_history_cross_channel_included metric events for observability.
"""
from __future__ import annotations

import logging
import math
import re
from datetime import datetime, UTC
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.message import Message

logger = logging.getLogger(__name__)

# Minimal English stopwords for token-overlap precision (ADR-002 follow-up)
_STOPWORDS = frozenset(
    """
    a an the and or but if then else when at by for with about against between into through
    during before after above below to from up down in out on off over under again further
    then once here there all any both each few more most other some such no nor not only own
    same so than too very can will just should now
    """.split()
)


class TwinEngineService:
    """Core twin context and draft helpers."""

    # ------------------------------------------------------------------ #
    # Short-term history (ADR-002)                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_reference_tokens(text: str) -> set[str]:
        """Lowercase content words longer than 2 chars, stopwords removed."""
        if not text:
            return set()
        tokens = re.findall(r"[a-zA-Z0-9']+", text.lower())
        return {t for t in tokens if len(t) > 2 and t not in _STOPWORDS}

    @staticmethod
    def _token_overlap(a: str, b: str) -> float:
        """Jaccard-like token overlap between two texts (0.0-1.0)."""
        ta = TwinEngineService._extract_reference_tokens(a)
        tb = TwinEngineService._extract_reference_tokens(b)
        if not ta or not tb:
            return 0.0
        inter = len(ta & tb)
        return inter / max(len(ta | tb), 1)

    @staticmethod
    def _score_history_message(
        msg: Message,
        incoming: str,
        rank: int,
        pool_size: int,
    ) -> float:
        """Hybrid score: recency_weight * recency + overlap_weight * token_overlap.

        Recency is rank-based by default. When hybrid_history_use_time_based_recency is true,
        it uses exponential decay from message age with configurable half-life.
        Weights come from settings (defaults 0.7 / 0.3) so operators can tune without code changes.
        """
        recency_w = float(getattr(settings, "hybrid_history_recency_weight", 0.7) or 0.7)
        overlap_w = float(getattr(settings, "hybrid_history_overlap_weight", 0.3) or 0.3)
        # Normalize if they do not sum to ~1.0
        total = recency_w + overlap_w
        if total <= 0:
            recency_w, overlap_w = 0.7, 0.3
        else:
            recency_w /= total
            overlap_w /= total

        use_time = bool(getattr(settings, "hybrid_history_use_time_based_recency", False))
        if use_time:
            created = getattr(msg, "created_at", None)
            if created is None:
                recency = 0.5
            else:
                now = datetime.now(UTC)
                if created.tzinfo is None:
                    created = created.replace(tzinfo=UTC)
                age_days = max(0.0, (now - created).total_seconds() / 86400.0)
                half_life = float(getattr(settings, "hybrid_history_recency_half_life_days", 7.0) or 7.0)
                half_life = max(0.1, half_life)
                # Exponential decay: 1.0 at age=0, 0.5 at half_life days
                recency = math.pow(0.5, age_days / half_life)
                recency = max(0.1, min(1.0, recency))
        else:
            # Rank-based (original): 1.0 for most recent, decays linearly to ~0.3 at the far end
            if pool_size <= 1:
                recency = 1.0
            else:
                recency = 1.0 - 0.7 * (rank / max(pool_size - 1, 1))
            recency = max(0.3, min(1.0, recency))

        # Overlap
        incoming_tokens = TwinEngineService._extract_reference_tokens(incoming)
        msg_tokens = TwinEngineService._extract_reference_tokens(getattr(msg, "content", "") or "")
        if not incoming_tokens or not msg_tokens:
            overlap = 0.0
        else:
            overlap = len(incoming_tokens & msg_tokens) / max(len(incoming_tokens), 1)

        return recency_w * recency + overlap_w * overlap

    @staticmethod
    def _load_hybrid_history(db: Session, incoming: Message, user_id: str) -> list[Message]:
        """Load last N (configurable), score, return top K (configurable) that meet min score.

        Optionally applies a diversity filter when hybrid_history_diversity_threshold > 0.
        Optionally includes cross-channel messages when hybrid_history_cross_channel is true.
        Falls back to pure recency on error or if no messages meet the min score threshold.
        Emits a structured hybrid_history_selection metric for observability.
        Emits hybrid_history_fallback on fallback paths.
        Emits hybrid_history_diversity_skipped when the diversity filter drops messages.
        Emits hybrid_history_cross_channel_included when cross-channel messages are selected.
        """
        pool_size = max(5, int(getattr(settings, "hybrid_history_pool_size", 20) or 20))
        top_k = max(1, int(getattr(settings, "hybrid_history_top_k", 5) or 5))
        min_score = float(getattr(settings, "hybrid_history_min_score", 0.0) or 0.0)
        diversity_thresh = float(getattr(settings, "hybrid_history_diversity_threshold", 0.0) or 0.0)
        cross_channel = bool(getattr(settings, "hybrid_history_cross_channel", False))
        try:
            filters = [
                Message.user_id == user_id,
                Message.sender_id == incoming.sender_id,
                Message.id != incoming.id,
            ]
            if not cross_channel:
                filters.append(Message.channel == incoming.channel)

            pool = (
                db.query(Message)
                .filter(*filters)
                .order_by(Message.created_at.desc())
                .limit(pool_size)
                .all()
            )
            if len(pool) <= top_k and min_score <= 0.0 and diversity_thresh <= 0.0:
                return pool[:top_k]

            scored = [
                (TwinEngineService._score_history_message(m, incoming.content or "", rank, len(pool)), m)
                for rank, m in enumerate(pool)
            ]
            scored.sort(key=lambda x: x[0], reverse=True)

            # Apply min score filter
            if min_score > 0.0:
                candidates = [(s, m) for s, m in scored if s >= min_score]
                if not candidates:
                    logger.debug("hybrid_history_no_messages_met_min_score min=%.2f falling_back", min_score)
                    payload = {
                        "metric": "hybrid_history_fallback",
                        "reason": "min_score_not_met",
                        "min_score": min_score,
                    }
                    logger.info(
                        "hybrid_history_fallback reason=min_score_not_met min_score=%.2f",
                        min_score,
                        extra=payload,
                    )
                    return TwinEngineService._load_recent_history(db, incoming, user_id, limit=top_k)
            else:
                candidates = scored

            # Apply optional diversity filter (greedy)
            skipped_by_diversity = 0
            if diversity_thresh > 0.0 and candidates:
                selected: list[tuple[float, Message]] = []
                for score, msg in candidates:
                    content = getattr(msg, "content", "") or ""
                    if any(
                        TwinEngineService._token_overlap(content, getattr(sel[1], "content", "") or "") > diversity_thresh
                        for sel in selected
                    ):
                        skipped_by_diversity += 1
                        continue
                    selected.append((score, msg))
                    if len(selected) >= top_k:
                        break
                top = [m for _, m in selected]
                qualified_count = len(candidates)
                if skipped_by_diversity > 0:
                    payload = {
                        "metric": "hybrid_history_diversity_skipped",
                        "skipped_count": skipped_by_diversity,
                        "diversity_threshold": diversity_thresh,
                        "selected_count": len(top),
                    }
                    logger.info(
                        "hybrid_history_diversity_skipped skipped=%d threshold=%.2f selected=%d",
                        skipped_by_diversity,
                        diversity_thresh,
                        len(top),
                        extra=payload,
                    )
            else:
                top = [m for _, m in candidates[:top_k]]
                qualified_count = len(candidates)

            # Count cross-channel messages if the feature is enabled
            cross_channel_count = 0
            if cross_channel and top:
                cross_channel_count = sum(
                    1 for m in top if getattr(m, "channel", None) is not None and getattr(m, "channel", None) != incoming.channel
                )
                if cross_channel_count > 0:
                    cc_payload = {
                        "metric": "hybrid_history_cross_channel_included",
                        "cross_channel_count": cross_channel_count,
                        "selected_count": len(top),
                    }
                    logger.info(
                        "hybrid_history_cross_channel_included count=%d selected=%d",
                        cross_channel_count,
                        len(top),
                        extra=cc_payload,
                    )

            # Structured observability metric (always emitted at INFO when hybrid runs)
            top_score = scored[0][0] if scored else 0.0
            selected_count = len(top)
            payload = {
                "metric": "hybrid_history_selection",
                "pool_size": len(pool),
                "qualified_count": qualified_count,
                "selected_count": selected_count,
                "top_score": round(top_score, 4),
                "min_score": min_score,
                "diversity_threshold": diversity_thresh,
                "cross_channel": cross_channel,
                "cross_channel_count": cross_channel_count,
            }
            logger.info(
                "hybrid_history_selection pool=%d qualified=%d selected=%d top_score=%.3f min_score=%.2f diversity=%.2f cross_channel=%s cross_count=%d",
                len(pool),
                qualified_count,
                selected_count,
                top_score,
                min_score,
                diversity_thresh,
                cross_channel,
                cross_channel_count,
                extra=payload,
            )

            if logger.isEnabledFor(logging.DEBUG):
                top_scores = [(s, (m.content or "")[:60]) for s, m in scored[:3]]
                logger.debug("hybrid_history_top_scores pool=%d top_k=%d min_score=%.2f diversity=%.2f cross=%s %s", pool_size, top_k, min_score, diversity_thresh, cross_channel, top_scores)

            return top
        except Exception as exc:  # noqa: BLE001
            logger.warning("hybrid_history_failed falling_back_to_recency: %s", exc)
            payload = {
                "metric": "hybrid_history_fallback",
                "reason": "exception",
                "error": str(exc)[:200],
            }
            logger.info(
                "hybrid_history_fallback reason=exception",
                extra=payload,
            )
            return TwinEngineService._load_recent_history(db, incoming, user_id, limit=top_k)

    @staticmethod
    def _load_recent_history(db: Session, incoming: Message, user_id: str, limit: int = 5) -> list[Message]:
        """Pure recency path (production default)."""
        return (
            db.query(Message)
            .filter(
                Message.user_id == user_id,
                Message.sender_id == incoming.sender_id,
                Message.channel == incoming.channel,
                Message.id != incoming.id,
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def _format_relative_time(created_at: datetime | None) -> str:
        """Human-readable relative time for history prompts."""
        if not created_at:
            return "unknown time"
        now = datetime.now(UTC)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        delta = now - created_at
        seconds = delta.total_seconds()
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            mins = int(seconds // 60)
            return f"{mins}m ago"
        if seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours}h ago"
        days = int(seconds // 86400)
        if days == 1:
            return "yesterday"
        if days < 7:
            return f"{days}d ago"
        if days < 14:
            return "last week"
        return f"{days}d ago"

    @staticmethod
    def _build_history_prompt(messages: list[Message]) -> str:
        """Format short-term history with relative timestamps for the LLM.

        Optionally truncates to hybrid_history_prompt_max_chars (0 = no limit) and emits a metric.
        """
        if not messages:
            return ""
        lines = ["Recent conversation history (most relevant first):"]
        for m in messages:
            rel = TwinEngineService._format_relative_time(getattr(m, "created_at", None))
            content = (getattr(m, "content", "") or "").strip().replace("\n", " ")
            lines.append(f"- [{rel}] {content[:300]}")
        prompt = "\n".join(lines)

        max_chars = int(getattr(settings, "hybrid_history_prompt_max_chars", 0) or 0)
        if max_chars > 0 and len(prompt) > max_chars:
            original_len = len(prompt)
            # Truncate at a line boundary if possible
            truncated = prompt[:max_chars]
            last_newline = truncated.rfind("\n")
            if last_newline > max_chars * 0.7:
                truncated = truncated[:last_newline]
            prompt = truncated + "\n[... history truncated for length]"
            payload = {
                "metric": "hybrid_history_prompt_truncated",
                "original_chars": original_len,
                "truncated_chars": len(prompt),
                "max_chars": max_chars,
            }
            logger.info(
                "hybrid_history_prompt_truncated original=%d truncated=%d max=%d",
                original_len,
                len(prompt),
                max_chars,
                extra=payload,
            )

        return prompt

    # ------------------------------------------------------------------ #
    # Context loading entry point                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_context(db: Session, incoming: Message, user_id: str) -> dict[str, Any]:
        """Load profile, briefings, and short-term history (hybrid or pure)."""
        if settings.feature_hybrid_history:
            history = TwinEngineService._load_hybrid_history(db, incoming, user_id)
        else:
            history = TwinEngineService._load_recent_history(db, incoming, user_id, limit=5)

        return {
            "history": history,
            "history_prompt": TwinEngineService._build_history_prompt(history),
            # Other context fields (profile, briefings, etc.) would be loaded here in the full engine
        }

    # ------------------------------------------------------------------ #
    # Prompt construction (minimal surface used by tests / graph)         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_prompts(context: dict[str, Any], incoming_content: str) -> tuple[str, str]:
        """Return (system, user) prompts. History with relative times is injected."""
        history_block = context.get("history_prompt") or ""
        user = f"{history_block}\n\nIncoming message:\n{incoming_content}".strip()
        system = "You are the user's digital twin. Draft a reply in their voice. Never invent facts."
        return system, user
