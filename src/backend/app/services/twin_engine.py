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
import json
import logging
import time
from sqlalchemy.orm import Session
from app.models import Message, Twin, IdentityProfile, Topic
from app.services.moderation import ModerationService
from app.config import get_settings

try:
    from litellm import completion
except Exception:  # pragma: no cover
    completion = None


logger = logging.getLogger(__name__)
settings = get_settings()


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
    history: list[Message]
    constraints: ChannelConstraints


class TwinEngineService:
    """Twin Engine orchestration for draft generation."""

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
        if completion is None:
            raise RuntimeError("litellm not available")

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

        return TwinContext(
            message=message,
            twin=twin,
            identity=identity,
            known_topics=known_topics,
            avoided_topics=avoided_topics,
            history=history,
            constraints=constraints,
        )

    @staticmethod
    def _build_prompts(ctx: TwinContext) -> tuple[str, str]:
        system_prompt = (
            f"You are the digital twin of this user. "
            f"Tone={ctx.twin.tone}; Domain={ctx.twin.domain}; "
            f"AvgLength={ctx.twin.avg_response_length}; "
            f"ChannelHint={ctx.constraints.style_hint}; "
            f"AvoidedTopics={', '.join(ctx.avoided_topics) or 'none'}."
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

        if ctx.message.channel == "gmail":
            opening = f"Hi {ctx.message.sender_name},"
            body = "Thanks for your message. I appreciate you reaching out."
            follow_up = "Here is a quick response from my side based on what you shared."
            closing = "Best regards"
            draft = f"{opening}\n\n{body} {follow_up}\n\n{closing}"
        else:
            body = "Thanks for the message. I appreciate you reaching out and sharing this."
            follow_up = "Happy to help and continue the conversation from here."
            draft = f"Hey {ctx.message.sender_name}! {body} {follow_up}"

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
        Run Phase 2 Twin Engine v1 for a message.

        Returns a dict with draft output, confidence metadata, and moderation result.
        """
        pipeline_start = time.perf_counter()

        message = db.query(Message).filter(Message.id == message_id, Message.user_id == user_id).first()
        if not message:
            raise ValueError("Message not found")

        ctx = TwinEngineService._load_context(db, message, user_id)
        system_prompt, user_prompt = TwinEngineService._build_prompts(ctx)
        draft, factors, generator_reasoning, generator_flags, generation_source, generation_metrics = TwinEngineService._generate_draft(
            ctx,
            system_prompt,
            user_prompt,
        )

        confidence_score = TwinEngineService._compute_overall_confidence(factors)
        confidence_label = ModerationService.get_confidence_label(confidence_score)

        moderation_passed, flags, risk_score = ModerationService.check_content_safety(draft)

        if not moderation_passed:
            confidence_score = min(confidence_score, 0.3)
            confidence_label = ModerationService.get_confidence_label(confidence_score)

        reasoning = (
            f"{generator_reasoning} Generated with channel='{message.channel}', "
            f"topic_known={factors['topic_known']}, no_avoided_topics={factors['no_avoided_topics']}, "
            f"moderation_risk={risk_score}."
        )

        pipeline_latency_ms = int((time.perf_counter() - pipeline_start) * 1000)
        metrics = {
            "pipeline_latency_ms": pipeline_latency_ms,
            "llm_latency_ms": generation_metrics.get("llm_latency_ms", 0),
            "parse_retry_count": generation_metrics.get("parse_retry_count", 0),
            "llm_calls": generation_metrics.get("llm_calls", 0),
            "used_fallback": generation_source != "llm",
        }

        logger.info(
            "Twin pipeline completed message_id=%s user_id=%s source=%s confidence=%.2f moderation_passed=%s pipeline_latency_ms=%s llm_latency_ms=%s parse_retry_count=%s",
            message.id,
            user_id,
            generation_source,
            confidence_score,
            moderation_passed,
            metrics["pipeline_latency_ms"],
            metrics["llm_latency_ms"],
            metrics["parse_retry_count"],
        )

        return {
            "twin_id": ctx.twin.id,
            "draft": draft,
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
            "confidence_reasoning": reasoning,
            "confidence_factors": factors,
            "moderation_passed": moderation_passed,
            "moderation_flags": flags + generator_flags,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "generation_source": generation_source,
            "metrics": metrics,
        }
