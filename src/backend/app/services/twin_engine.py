"""
Twin Engine service (Phase 2 v1)

Implements a deterministic draft pipeline with:
- Context loading (identity + topics + recent history)
- Channel-aware response shaping
- Confidence factor scoring
- Safety fallback for avoided topics

This is intentionally provider-agnostic so we can later swap draft generation
with LiteLLM/Claude while preserving the same pipeline contract.
"""

from dataclasses import dataclass
from datetime import datetime, UTC
import json
import logging
import time
from sqlalchemy.orm import Session
from app.models import Message, Twin, IdentityProfile, Topic, TwinBriefing
from app.services.fallback_drafter import DraftInputs, build_fallback_draft
from app.services.moderation import ModerationService
from app.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()

# Common English stopwords (length >=4) to improve hybrid token overlap precision.
# Keeps the scorer lightweight and dependency-free.
_HYBRID_STOPWORDS = frozenset({
    "this", "that", "with", "from", "have", "been", "were", "they", "what", "when",
    "where", "which", "there", "their", "about", "would", "could", "should", "your",
    "will", "just", "more", "some", "than", "them", "then", "into", "also", "only",
    "very", "much", "many", "most", "such", "like", "make", "made", "want", "need",
    "know", "think", "going", "good", "well", "back", "time", "year", "work", "here",
})

# Estimated USD per 1M tokens (approx placeholders; tune per provider billing).
MODEL_COST_PER_MILLION = {
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "gpt-5": {"input": 5.0, "output": 15.0},
}


@dataclass
class ChannelConstraints:
    style_hint: str
    max_words: int
    emoji_multiplier: float
    formality_adjustment: int


CHANNEL_CONSTRAINTS = {
    "instagram_dm": ChannelConstraints(
        style_hint="casual, warm, short",
        max_words=150,
        emoji_multiplier=1.2,
        formality_adjustment=-1,
    ),
    "gmail": ChannelConstraints(
        style_hint="professional, structured, clear",
        max_words=300,
        emoji_multiplier=0.2,
        formality_adjustment=1,
    ),
    "twitter_dm": ChannelConstraints(
        style_hint="concise, punchy, direct",
        max_words=100,
        emoji_multiplier=1.0,
        formality_adjustment=0,
    ),
    "whatsapp": ChannelConstraints(
        style_hint="conversational, warm",
        max_words=120,
        emoji_multiplier=1.1,
        formality_adjustment=-1,
    ),
}


@dataclass
class TwinContext:
    message: Message
    twin: Twin
    identity: IdentityProfile
    known_topics: list[str]
    avoided_topics: list[str]
    active_briefings: list[TwinBriefing]
    history: list[Message]
    constraints: ChannelConstraints


class TwinEngineService:
    """Twin Engine orchestration for draft generation."""

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        # Heuristic: ~4 chars/token, minimum 1 token for non-empty text.
        if not text:
            return 0
        return max(1, int(len(text) / 4))

    @staticmethod
    def _estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
        rates = MODEL_COST_PER_MILLION.get(model, {"input": 3.0, "output": 15.0})
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]
        return round(input_cost + output_cost, 8)

    @staticmethod
    def _extract_json_object(text: str) -> dict:
        """Extract and parse first JSON object found in model output."""
        text = text.strip()
        if text.startswith("{") and text.endswith("}"):
            return json.loads(text)

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in model output")
        return json.loads(text[start:end + 1])

    @staticmethod
    def _build_llm_messages(system_prompt: str, user_prompt: str) -> list[dict]:
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    user_prompt
                    + "\n\nReturn ONLY valid JSON with this exact shape:\n"
                      "{\"draft\": string|null, \"confidence_factors\": {\"topic_known\": number, \"length_match\": number, \"tone_match\": number, \"no_avoided_topics\": number, \"sample_similarity\": number}, \"reasoning\": string, \"flags\": []}"
                ),
            },
        ]

    @staticmethod
    def _call_litellm(messages: list[dict]) -> str:
        try:
            from litellm import completion
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("litellm not available") from exc

        response = completion(
            model=settings.default_llm_model,
            messages=messages,
            temperature=settings.twin_llm_temperature,
            max_tokens=settings.twin_llm_max_tokens,
            timeout=settings.twin_llm_timeout_seconds,
        )
        return response.choices[0].message.content

    @staticmethod
    def _generate_draft_via_llm(system_prompt: str, user_prompt: str) -> tuple[str, dict, str, list, dict]:
        llm_latency_ms = 0
        parse_retry_count = 0

        messages = TwinEngineService._build_llm_messages(system_prompt, user_prompt)
        llm_start = time.perf_counter()
        raw = TwinEngineService._call_litellm(messages)
        llm_latency_ms += int((time.perf_counter() - llm_start) * 1000)

        try:
            parsed = TwinEngineService._extract_json_object(raw)
        except Exception:
            if not settings.feature_twin_llm_json_retry:
                raise

            parse_retry_count += 1

            retry_messages = [
                {"role": "system", "content": "Return valid JSON only. Do not add any commentary."},
                {
                    "role": "user",
                    "content": (
                        "Your previous response was not valid JSON. "
                        "Rewrite it as valid JSON with keys: draft, confidence_factors, reasoning, flags."
                    ),
                },
            ]
            llm_start = time.perf_counter()
            raw = TwinEngineService._call_litellm(retry_messages)
            llm_latency_ms += int((time.perf_counter() - llm_start) * 1000)
            parsed = TwinEngineService._extract_json_object(raw)

        draft = parsed.get("draft")
        if not isinstance(draft, str) or not draft.strip():
            raise ValueError("LLM JSON missing non-empty 'draft'")

        factors = parsed.get("confidence_factors") or {}
        normalized = {
            "topic_known": float(factors.get("topic_known", 0.5)),
            "length_match": float(factors.get("length_match", 0.5)),
            "tone_match": float(factors.get("tone_match", 0.5)),
            "no_avoided_topics": float(factors.get("no_avoided_topics", 1.0)),
            "sample_similarity": float(factors.get("sample_similarity", 0.5)),
        }
        for key in normalized:
            normalized[key] = max(0.0, min(1.0, round(normalized[key], 2)))

        reasoning = str(parsed.get("reasoning", "Generated by LLM."))
        flags = parsed.get("flags") if isinstance(parsed.get("flags"), list) else []
        metrics = {
            "llm_latency_ms": llm_latency_ms,
            "parse_retry_count": parse_retry_count,
            "llm_calls": parse_retry_count + 1,
        }
        return draft, normalized, reasoning, flags, metrics

    @staticmethod
    def _score_history_message(msg: Message, incoming_content: str, rank: int, pool_size: int) -> float:
        """Hybrid score: 0.7 recency decay + 0.3 token overlap. Higher is better."""
        # Recency: 1.0 for most recent (rank 0), decaying linearly
        recency = max(0.0, 1.0 - (rank / max(pool_size, 1)))
        # Token overlap with incoming message
        incoming_tokens = set(TwinEngineService._extract_reference_tokens(incoming_content))
        msg_tokens = set(TwinEngineService._extract_reference_tokens(msg.content or ""))
        overlap = len(incoming_tokens & msg_tokens) / max(len(incoming_tokens), 1) if incoming_tokens else 0.0
        return 0.7 * recency + 0.3 * overlap

    @staticmethod
    def _load_hybrid_history(db: Session, message: Message, user_id: str) -> list[Message]:
        """Load top-5 history by hybrid score from a pool of 20 recent messages."""
        pool = db.query(Message).filter(
            Message.user_id == user_id,
            Message.sender_id == message.sender_id,
            Message.channel == message.channel,
            Message.id != message.id,
        ).order_by(Message.created_at.desc()).limit(20).all()

        if len(pool) <= 5:
            return pool

        logger.debug(
            "Hybrid history: scoring %d candidates for message_id=%s (feature_hybrid_history=on)",
            len(pool),
            message.id,
        )
        scored = [
            (TwinEngineService._score_history_message(m, message.content or "", i, len(pool)), m)
            for i, m in enumerate(pool)
        ]
        # Highest score first; stable for ties by original order (already recent-first)
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:5]]

    @staticmethod
    def _load_context(db: Session, message: Message, user_id: str) -> TwinContext:
        twin = db.query(Twin).filter(Twin.user_id == user_id).first()
        identity = db.query(IdentityProfile).filter(IdentityProfile.user_id == user_id).first()

        if not twin:
            raise ValueError("Twin not found")
        if not identity:
            raise ValueError("Identity profile not found")

        known_topics = [
            t.topic.lower() for t in db.query(Topic).filter(
                Topic.user_id == user_id,
                Topic.topic_type == "known",
            ).all()
        ]
        avoided_topics = [
            t.topic.lower() for t in db.query(Topic).filter(
                Topic.user_id == user_id,
                Topic.topic_type == "avoided",
            ).all()
        ]

        if settings.feature_hybrid_history:
            history = TwinEngineService._load_hybrid_history(db, message, user_id)
        else:
            history = db.query(Message).filter(
                Message.user_id == user_id,
                Message.sender_id == message.sender_id,
                Message.channel == message.channel,
                Message.id != message.id,
            ).order_by(Message.created_at.desc()).limit(5).all()

        constraints = CHANNEL_CONSTRAINTS.get(
            message.channel,
            ChannelConstraints(
                style_hint="neutral, clear",
                max_words=150,
                emoji_multiplier=1.0,
                formality_adjustment=0,
            ),
        )

        now_dt = datetime.now(UTC).replace(tzinfo=None)
        briefing_rows = db.query(TwinBriefing).filter(
            TwinBriefing.user_id == user_id,
            TwinBriefing.is_active.is_(True),
            TwinBriefing.cleared_at.is_(None),
        ).order_by(
            TwinBriefing.priority.desc(),
            TwinBriefing.created_at.desc(),
        ).all()

        active_briefings = [
            b for b in briefing_rows
            if (b.expires_at is None or b.expires_at > now_dt)
            and (b.max_uses is None or b.use_count < b.max_uses)
        ]

        return TwinContext(
            message=message,
            twin=twin,
            identity=identity,
            known_topics=known_topics,
            avoided_topics=avoided_topics,
            active_briefings=active_briefings,
            history=history,
            constraints=constraints,
        )

    @staticmethod
    def _build_prompts(ctx: TwinContext) -> tuple[str, str]:
        briefing_block = ""
        if ctx.active_briefings:
            lines = [
                f"[{b.briefing_type.upper()}|P{b.priority}] {b.content}"
                for b in ctx.active_briefings
            ]
            briefing_block = " ActiveBriefings=" + " || ".join(lines)

        system_prompt = (
            f"You are the digital twin of this user. "
            f"Tone={ctx.twin.tone}; Domain={ctx.twin.domain}; "
            f"AvgLength={ctx.twin.avg_response_length}; "
            f"ChannelHint={ctx.constraints.style_hint}; "
            f"AvoidedTopics={', '.join(ctx.avoided_topics) or 'none'}."
            f"{briefing_block}"
        )

        history_preview = " | ".join([m.content[:80] for m in reversed(ctx.history)])
        user_prompt = (
            f"Incoming message from {ctx.message.sender_name}: {ctx.message.content}\n"
            f"History: {history_preview or 'No prior history'}"
        )

        return system_prompt, user_prompt

    @staticmethod
    def _contains_avoided_topic(content: str, avoided_topics: list[str]) -> bool:
        lower = content.lower()
        return any(topic and topic in lower for topic in avoided_topics)

    @staticmethod
    def _topic_match_score(content: str, known_topics: list[str]) -> float:
        if not known_topics:
            return 0.5
        lower = content.lower()
        if any(topic and topic in lower for topic in known_topics):
            return 0.9
        return 0.45

    @staticmethod
    def _apply_word_limit(text: str, max_words: int) -> str:
        words = text.split()
        if len(words) <= max_words:
            return text
        return " ".join(words[:max_words]).rstrip() + "..."

    @staticmethod
    def _extract_reference_tokens(text: str) -> list[str]:
        """Extract simple keyword tokens for briefing reference matching and hybrid scoring.

        Filters short tokens and a small stopword set so overlap scoring focuses on content words.
        """
        tokens = []
        for raw in text.lower().split():
            cleaned = "".join(ch for ch in raw if ch.isalnum())
            if len(cleaned) >= 4 and cleaned not in _HYBRID_STOPWORDS:
                tokens.append(cleaned)
        return list(dict.fromkeys(tokens))

    @staticmethod
    def _get_referenced_briefings(ctx: TwinContext, draft: str) -> list[TwinBriefing]:
        """Return briefings that appear referenced by incoming message or generated draft."""
        if not ctx.active_briefings:
            return []

        search_space = f"{ctx.message.content}\n{draft}".lower()
        referenced: list[TwinBriefing] = []

        for briefing in ctx.active_briefings:
            topic_tokens = TwinEngineService._extract_reference_tokens(briefing.topic)
            content_tokens = TwinEngineService._extract_reference_tokens(briefing.content)
            # Cap content token scan to keep matching cheap and deterministic.
            candidate_tokens = list(dict.fromkeys(topic_tokens + content_tokens[:12]))

            if any(token in search_space for token in candidate_tokens):
                referenced.append(briefing)

        return referenced

    @staticmethod
    def _increment_briefing_use_counts(db: Session, briefings: list[TwinBriefing]) -> None:
        """Increment use_count for referenced briefings and deactivate when max uses reached."""
        if not briefings:
            return

        now = datetime.now(UTC).replace(tzinfo=None)
        for briefing in briefings:
            briefing.use_count = (briefing.use_count or 0) + 1
            if briefing.max_uses is not None and briefing.use_count >= briefing.max_uses:
                briefing.is_active = False
                if briefing.cleared_at is None:
                    briefing.cleared_at = now
            db.add(briefing)

        db.commit()

    @staticmethod
    def _generate_draft(ctx: TwinContext, system_prompt: str, user_prompt: str) -> tuple[str, dict, str, list, str, dict]:
        if TwinEngineService._contains_avoided_topic(ctx.message.content, ctx.avoided_topics):
            draft = "That's not something I cover — let me get back to you"
            factors = {
                "topic_known": 0.2,
                "length_match": 1.0,
                "tone_match": 0.7,
                "no_avoided_topics": 0.0,
                "sample_similarity": 0.5,
            }
            return draft, factors, "Avoided topic fallback", [], "deterministic", {
                "llm_latency_ms": 0,
                "parse_retry_count": 0,
                "llm_calls": 0,
                "fallback_reason": "avoided_topic",
            }

        if settings.feature_twin_llm_drafts:
            try:
                llm_draft, llm_factors, llm_reasoning, llm_flags, llm_metrics = TwinEngineService._generate_draft_via_llm(
                    system_prompt,
                    user_prompt,
                )
                llm_draft = TwinEngineService._apply_word_limit(llm_draft, ctx.constraints.max_words)
                return llm_draft, llm_factors, llm_reasoning, llm_flags, "llm", llm_metrics
            except Exception as exc:
                logger.warning("LLM draft generation failed, using deterministic fallback: %s", exc)

        draft = build_fallback_draft(
            DraftInputs(
                sender_name=ctx.message.sender_name,
                content=ctx.message.content,
                channel=ctx.message.channel,
                tone=ctx.twin.tone,
                avg_response_length=ctx.twin.avg_response_length,
                known_topics=ctx.known_topics,
                availability_notes=[
                    b.content for b in ctx.active_briefings if b.briefing_type == "availability"
                ],
            )
        )

        draft = TwinEngineService._apply_word_limit(draft, ctx.constraints.max_words)

        target_len = max(ctx.twin.avg_response_length, 1)
        actual_len = max(len(draft.split()), 1)
        length_delta = abs(actual_len - target_len) / target_len
        length_match = max(0.0, min(1.0, 1.0 - length_delta))

        factors = {
            "topic_known": TwinEngineService._topic_match_score(ctx.message.content, ctx.known_topics),
            "length_match": round(length_match, 2),
            "tone_match": 0.8 if ctx.twin.tone else 0.6,
            "no_avoided_topics": 1.0,
            "sample_similarity": 0.7 if ctx.history else 0.5,
        }
        return draft, factors, "Generated by deterministic fallback engine", [], "deterministic", {
            "llm_latency_ms": 0,
            "parse_retry_count": 0,
            "llm_calls": 0,
            "fallback_reason": "llm_unavailable_or_disabled" if settings.feature_twin_llm_drafts else "llm_disabled",
        }

    @staticmethod
    def _compute_overall_confidence(factors: dict) -> float:
        # Weighted average aligned with Phase 2 confidence factors.
        score = (
            0.30 * factors["topic_known"] +
            0.20 * factors["length_match"] +
            0.20 * factors["tone_match"] +
            0.20 * factors["no_avoided_topics"] +
            0.10 * factors["sample_similarity"]
        )
        return round(max(0.0, min(1.0, score)), 2)

    @staticmethod
    def run_twin_pipeline(db: Session, message_id: str, user_id: str) -> dict:
        """
        Produce a draft for a message: the live Twin Engine.

        Runs the LangGraph engine (context -> generate -> moderate -> bookkeeping -> route -> audit)
        and returns the draft, confidence, moderation result and metrics. Every run writes a
        structured audit event. Raises ValueError if no draft could be produced.
        """
        from app.services.twin_langgraph import run_twin_graph  # local import: the graph builds on this class

        return run_twin_graph(db, message_id, user_id)
