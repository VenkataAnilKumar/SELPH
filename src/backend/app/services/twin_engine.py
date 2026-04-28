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
from sqlalchemy.orm import Session
from app.models import Message, Twin, IdentityProfile, Topic
from app.services.moderation import ModerationService


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
    def _generate_draft(ctx: TwinContext) -> tuple[str, dict]:
        if TwinEngineService._contains_avoided_topic(ctx.message.content, ctx.avoided_topics):
            draft = "That's not something I cover — let me get back to you"
            factors = {
                "topic_known": 0.2,
                "length_match": 1.0,
                "tone_match": 0.7,
                "no_avoided_topics": 0.0,
                "sample_similarity": 0.5,
            }
            return draft, factors

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
        return draft, factors

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
        message = db.query(Message).filter(Message.id == message_id, Message.user_id == user_id).first()
        if not message:
            raise ValueError("Message not found")

        ctx = TwinEngineService._load_context(db, message, user_id)
        system_prompt, user_prompt = TwinEngineService._build_prompts(ctx)
        draft, factors = TwinEngineService._generate_draft(ctx)

        confidence_score = TwinEngineService._compute_overall_confidence(factors)
        confidence_label = ModerationService.get_confidence_label(confidence_score)

        moderation_passed, flags, risk_score = ModerationService.check_content_safety(draft)

        if not moderation_passed:
            confidence_score = min(confidence_score, 0.3)
            confidence_label = ModerationService.get_confidence_label(confidence_score)

        reasoning = (
            f"Generated with channel='{message.channel}', topic_known={factors['topic_known']}, "
            f"no_avoided_topics={factors['no_avoided_topics']}, moderation_risk={risk_score}."
        )

        return {
            "twin_id": ctx.twin.id,
            "draft": draft,
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
            "confidence_reasoning": reasoning,
            "confidence_factors": factors,
            "moderation_passed": moderation_passed,
            "moderation_flags": flags,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }
