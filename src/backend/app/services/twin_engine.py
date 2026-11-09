"""Twin Engine — context loading, hybrid short-term memory, and prompt construction.

Implements ADR-002: pure recency (limit=5) by default; hybrid scoring behind
FEATURE_HYBRID_HISTORY. History prompts include relative timestamps.
Pool size is configurable via hybrid_history_pool_size.
"""
from __future__ import annotations

import logging
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
    def _score_history_message(
        msg: Message,
        incoming: str,
        rank: int,
        pool_size: int,
    ) -> float:
        """Hybrid score: 0.7 * recency_decay + 0.3 * token_overlap."""
        # Recency: 1.0 for most recent, decays linearly to ~0.3 at the far end
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

        return 0.7 * recency + 0.3 * overlap

    @staticmethod
    def _load_hybrid_history(db: Session, incoming: Message, user_id: str) -> list[Message]:
        """Load last N (configurable), score, return top 5. Falls back to pure recency on error."""
        pool_size = max(5, int(getattr(settings, "hybrid_history_pool_size", 20) or 20))
        try:
            pool = (
                db.query(Message)
                .filter(
                    Message.user_id == user_id,
                    Message.sender_id == incoming.sender_id,
                    Message.channel == incoming.channel,
                    Message.id != incoming.id,
                )
                .order_by(Message.created_at.desc())
                .limit(pool_size)
                .all()
            )
            if len(pool) <= 5:
                return pool[:5]

            scored = [
                (TwinEngineService._score_history_message(m, incoming.content or "", rank, len(pool)), m)
                for rank, m in enumerate(pool)
            ]
            scored.sort(key=lambda x: x[0], reverse=True)
            top = [m for _, m in scored[:5]]

            if logger.isEnabledFor(logging.DEBUG):
                top_scores = [(s, (m.content or "")[:60]) for s, m in scored[:3]]
                logger.debug("hybrid_history_top_scores pool=%d %s", pool_size, top_scores)

            return top
        except Exception as exc:  # noqa: BLE001
            logger.warning("hybrid_history_failed falling_back_to_recency: %s", exc)
            return TwinEngineService._load_recent_history(db, incoming, user_id, limit=5)

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
        """Format short-term history with relative timestamps for the LLM."""
        if not messages:
            return ""
        lines = ["Recent conversation history (most relevant first):"]
        for m in messages:
            rel = TwinEngineService._format_relative_time(getattr(m, "created_at", None))
            content = (getattr(m, "content", "") or "").strip().replace("\n", " ")
            lines.append(f"- [{rel}] {content[:300]}")
        return "\n".join(lines)

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
