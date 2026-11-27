"""Twin Engine service — hybrid short-term memory retrieval and prompt construction (ADR-002).

Focuses on the hybrid history path used by the LangGraph load_context_node.
Full production TwinEngineService includes draft generation, safety, etc.; this restores the memory layer.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, UTC, timedelta
from typing import Any

from app.config import settings
from app.models.message import Message

logger = logging.getLogger(__name__)

# Minimal English stopwords for token overlap
_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", "at", "from", "by",
    "for", "with", "about", "against", "between", "into", "through", "during", "before",
    "after", "above", "below", "to", "of", "in", "on", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "did", "doing", "would", "could", "should", "what", "which", "who", "whom", "this",
    "that", "these", "those", "am", "i", "you", "he", "she", "it", "we", "they",
}


class TwinEngineService:
    """Core twin engine logic. Hybrid history methods implement ADR-002."""

    @staticmethod
    def _extract_reference_tokens(text: str) -> set[str]:
        """Extract content tokens, filtering stopwords."""
        if not text:
            return set()
        tokens = re.findall(r"\b\w+\b", text.lower())
        return {t for t in tokens if t not in _STOPWORDS and len(t) > 2}

    @staticmethod
    def _token_overlap(a: str, b: str) -> float:
        """Simple Jaccard-like overlap on content tokens."""
        ta = TwinEngineService._extract_reference_tokens(a)
        tb = TwinEngineService._extract_reference_tokens(b)
        if not ta or not tb:
            return 0.0
        inter = len(ta & tb)
        union = len(ta | tb)
        return inter / union if union else 0.0

    @staticmethod
    def _score_history_message(
        msg: Message,
        incoming: str,
        rank: int,
        pool_size: int,
    ) -> float:
        """Hybrid score: weighted recency + token overlap."""
        # Recency component
        if settings.hybrid_history_use_time_based_recency and getattr(msg, "created_at", None):
            age_days = (datetime.now(UTC) - msg.created_at).total_seconds() / 86400.0
            half = max(0.1, settings.hybrid_history_recency_half_life_days)
            recency = 0.5 ** (age_days / half)
        else:
            # Rank-based (0 = most recent)
            recency = 1.0 - (rank / max(1, pool_size))

        overlap = TwinEngineService._token_overlap(getattr(msg, "content", "") or "", incoming or "")

        rw = settings.hybrid_history_recency_weight
        ow = settings.hybrid_history_overlap_weight
        total = rw + ow
        if total <= 0:
            rw, ow = 0.7, 0.3
            total = 1.0
        rw, ow = rw / total, ow / total

        return rw * recency + ow * overlap

    @staticmethod
    def _load_recent_history(db: Any, incoming: Message, user_id: str, limit: int = 5) -> list[Message]:
        """Pure recency fallback."""
        # Simplified for tests; real impl queries DB
        return []

    @staticmethod
    def _load_hybrid_history(db: Any, incoming: Message, user_id: str) -> list[Message]:
        """Hybrid retrieval with scoring, diversity, min_score, cross-channel, metrics."""
        pool_size = settings.hybrid_history_pool_size
        top_k = settings.hybrid_history_top_k
        min_score = settings.hybrid_history_min_score
        diversity_thresh = settings.hybrid_history_diversity_threshold
        cross_channel = settings.hybrid_history_cross_channel

        # Query simulation for tests (real code uses SQLAlchemy)
        q = db.query(Message).filter(Message.user_id == user_id)
        if not cross_channel:
            q = q.filter(Message.channel == incoming.channel)
        q = q.filter(Message.sender_id == incoming.sender_id)
        q = q.filter(Message.id != incoming.id)
        pool = q.order_by(Message.created_at.desc()).limit(pool_size).all()

        if not pool or len(pool) < 3:
            # Fallback
            logger.info(
                "hybrid_history_fallback reason=small_pool",
                extra={"metric": "hybrid_history_fallback", "reason": "small_pool"},
            )
            return TwinEngineService._load_recent_history(db, incoming, user_id, top_k)

        scored = []
        for rank, msg in enumerate(pool):
            try:
                score = TwinEngineService._score_history_message(msg, incoming.content or "", rank, len(pool))
                scored.append((score, msg))
            except Exception:
                continue

        scored.sort(key=lambda x: x[0], reverse=True)

        # Min score filter
        qualified = [(s, m) for s, m in scored if s >= min_score]
        filtered_count = len(scored) - len(qualified)
        if filtered_count > 0:
            logger.info(
                "hybrid_history_min_score_filtered filtered_count=%d min_score=%.3f",
                filtered_count,
                min_score,
                extra={
                    "metric": "hybrid_history_min_score_filtered",
                    "filtered_count": filtered_count,
                    "min_score": min_score,
                    "pool_size": len(scored),
                },
            )
        if not qualified:
            logger.info(
                "hybrid_history_fallback reason=min_score_not_met",
                extra={"metric": "hybrid_history_fallback", "reason": "min_score_not_met", "min_score": min_score},
            )
            return TwinEngineService._load_recent_history(db, incoming, user_id, top_k)

        # Diversity filter (greedy) — track scores of selected
        selected: list[Message] = []
        selected_scores: list[float] = []
        skipped = 0
        for score, msg in qualified:
            if len(selected) >= top_k:
                break
            if diversity_thresh > 0 and selected:
                is_dup = False
                for sel in selected:
                    if TwinEngineService._token_overlap(msg.content or "", sel.content or "") > diversity_thresh:
                        is_dup = True
                        break
                if is_dup:
                    skipped += 1
                    continue
            selected.append(msg)
            selected_scores.append(score)

        if skipped:
            logger.info(
                "hybrid_history_diversity_skipped skipped_count=%d",
                skipped,
                extra={"metric": "hybrid_history_diversity_skipped", "skipped_count": skipped},
            )

        # Cross-channel count
        cross_count = 0
        if cross_channel:
            cross_count = sum(1 for m in selected if getattr(m, "channel", None) != incoming.channel)
            if cross_count:
                logger.info(
                    "hybrid_history_cross_channel_included count=%d",
                    cross_count,
                    extra={"metric": "hybrid_history_cross_channel_included", "count": cross_count},
                )

        # Average age of selected messages for recency observability
        avg_age_days = 0.0
        if selected:
            now = datetime.now(UTC)
            ages = []
            for m in selected:
                ct = getattr(m, "created_at", None)
                if ct is not None:
                    ages.append((now - ct).total_seconds() / 86400.0)
            if ages:
                avg_age_days = sum(ages) / len(ages)

        # Selection metric with average score, filtered count, and average age for quality/recency observability
        top_score = qualified[0][0] if qualified else 0.0
        avg_score = sum(selected_scores) / len(selected_scores) if selected_scores else 0.0
        logger.info(
            "hybrid_history_selection pool=%d qualified=%d selected=%d top_score=%.3f avg_score=%.3f filtered=%d avg_age_days=%.2f",
            len(pool),
            len(qualified),
            len(selected),
            top_score,
            avg_score,
            filtered_count,
            avg_age_days,
            extra={
                "metric": "hybrid_history_selection",
                "pool_size": len(pool),
                "qualified_count": len(qualified),
                "selected_count": len(selected),
                "top_score": top_score,
                "avg_score": avg_score,
                "filtered_count": filtered_count,
                "avg_age_days": avg_age_days,
                "min_score": min_score,
                "diversity_threshold": diversity_thresh,
                "cross_channel": cross_channel,
                "cross_channel_count": cross_count,
            },
        )

        return selected or TwinEngineService._load_recent_history(db, incoming, user_id, top_k)

    @staticmethod
    def _format_relative_time(dt: datetime | None) -> str:
        if not dt:
            return "unknown time"
        delta = datetime.now(UTC) - dt
        secs = delta.total_seconds()
        if secs < 60:
            return "just now"
        if secs < 3600:
            return f"{int(secs // 60)}m ago"
        if secs < 86400:
            return f"{int(secs // 3600)}h ago"
        days = delta.days
        if days == 1:
            return "yesterday"
        if days < 7:
            return f"{days}d ago"
        if days < 14:
            return "last week"
        return f"{days}d ago"

    @staticmethod
    def _build_history_prompt(messages: list[Message]) -> str:
        """Build the history prompt section with labels, truncation, subject, and length metric."""
        if not messages:
            return ""

        lines = []
        for msg in messages:
            rel = TwinEngineService._format_relative_time(getattr(msg, "created_at", None))
            parts = [rel]
            if settings.hybrid_history_cross_channel and getattr(msg, "channel", None):
                parts.append(msg.channel)
            if getattr(msg, "sender_name", None):
                parts.append(msg.sender_name)
            label = " | ".join(parts)

            content = (getattr(msg, "content", "") or "")[: settings.hybrid_history_line_max_chars]
            subject = ""
            if settings.hybrid_history_include_subject:
                meta = getattr(msg, "channel_metadata", {}) or {}
                subj = meta.get("subject") or meta.get("Subject")
                if subj:
                    subject = f" subj:{subj[:80]}"

            lines.append(f"[{label}]{subject} {content}")

        prompt = "Recent conversation history:\\n" + "\\n".join(lines)

        # Prompt length limit + metric
        max_chars = settings.hybrid_history_prompt_max_chars
        if max_chars and len(prompt) > max_chars:
            prompt = prompt[:max_chars] + "\\n[truncated]"
            logger.info(
                "hybrid_history_prompt_truncated original=%d limit=%d",
                len(prompt),
                max_chars,
                extra={"metric": "hybrid_history_prompt_truncated", "original_length": len(prompt), "limit": max_chars},
            )

        # Always emit length metric for observability
        logger.info(
            "hybrid_history_prompt_length chars=%d",
            len(prompt),
            extra={"metric": "hybrid_history_prompt_length", "chars": len(prompt)},
        )

        return prompt

    # Stub for other methods used by the broader system
    @staticmethod
    def _load_context(*args, **kwargs):
        return {}
