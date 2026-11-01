"""
Intent-aware fallback drafter (no LLM required).

Used when no LLM is configured or the LLM call fails. It produces a short, honest
scaffold the user can approve or edit. It never invents facts, commitments, prices or
dates: for questions and requests it acknowledges the message and promises a follow-up
instead of answering for the user.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

_QUESTION_STARTERS = (
    "how", "what", "why", "when", "where", "which", "who",
    "can", "could", "would", "do", "does", "did", "is", "are", "will", "should",
)

_INTENT_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("business", ("collab", "partnership", "sponsor", "pricing", "price", "quote", "proposal",
                  "hire", "work together", "invoice", "contract", "budget", "rate")),
    ("meeting", ("call", "meet", "meeting", "schedule", "calendar", "coffee", "availability",
                 "available", "catch up", "zoom")),
    ("gratitude", ("thank", "thanks", "appreciate", "love your", "loved", "great talk",
                   "amazing", "awesome", "inspiring", "big fan", "blew my mind")),
]


@dataclass
class DraftInputs:
    sender_name: str
    content: str
    channel: str
    tone: str | None
    avg_response_length: int
    known_topics: list[str]
    availability_notes: list[str]


def detect_intent(content: str) -> str:
    """Classify an incoming message: business | meeting | question | gratitude | general."""
    text = content.lower().strip()
    for intent, keywords in _INTENT_KEYWORDS:
        if intent == "gratitude":
            continue  # checked after question so "love your talk, how do you...?" is a question
        if any(re.search(rf"\b{re.escape(k)}", text) for k in keywords):
            return intent
    if "?" in text or text.split(" ", 1)[0].strip(",.!") in _QUESTION_STARTERS:
        return "question"
    if any(re.search(rf"\b{re.escape(k)}", text) for k in _INTENT_KEYWORDS[2][1]):
        return "gratitude"
    return "general"


def first_name(sender_name: str) -> str:
    name = (sender_name or "").strip()
    if not name or "@" in name:
        return "there"
    return name.split()[0].strip(",.!")


def match_topic(content: str, known_topics: Iterable[str]) -> str | None:
    lower = content.lower()
    for topic in known_topics:
        if topic and topic.lower() in lower:
            return topic
    return None


def _greeting(name: str, tone: str, gmail: bool) -> str:
    tone = (tone or "").lower()
    if gmail:
        return f"Hello {name}," if "formal" in tone else f"Hi {name},"
    if "formal" in tone:
        return f"Hello {name},"
    if "direct" in tone:
        return f"Hi {name} —"
    if "casual" in tone or "humor" in tone:
        return f"Hey {name}!"
    return f"Hey {name}!"


def _body(intent: str, topic: str | None, tone: str, long_form: bool) -> list[str]:
    formal = "formal" in (tone or "").lower()
    about = f" about {topic}" if topic else ""
    sentences: list[str]

    if intent == "gratitude":
        sentences = [
            "Thank you, that really means a lot." if formal else "Thank you, that really means a lot to me!",
        ]
        if long_form:
            sentences.append(
                "Messages like yours are what keep me going."
                if not formal
                else "I appreciate you taking the time to write."
            )
    elif intent == "question":
        sentences = [
            f"Great question{about}.",
            "I want to give you a proper answer, so let me get back to you soon.",
        ]
        if long_form:
            sentences.append("If you can share a bit more context, that will help me be specific.")
    elif intent == "meeting":
        sentences = [
            "Happy to connect." if not formal else "I would be glad to connect.",
            "Let me check my calendar and come back to you with a couple of options.",
        ]
    elif intent == "business":
        sentences = [
            "Thanks for reaching out." if formal else "Thanks for reaching out, I appreciate it.",
            "I will review the details and get back to you shortly.",
        ]
        if long_form:
            sentences.append("In the meantime, feel free to send over anything that would help me understand the scope.")
    else:
        sentences = [
            f"Thanks for your message{about}." if formal else f"Thanks for the message{about}!",
            "I will follow up with you soon.",
        ]
    return sentences


def build_fallback_draft(inputs: DraftInputs) -> str:
    """Compose a tone- and length-aware scaffold reply. Pure function, no I/O."""
    tone = inputs.tone or ""
    gmail = inputs.channel == "gmail"
    name = first_name(inputs.sender_name)
    intent = detect_intent(inputs.content)
    topic = match_topic(inputs.content, inputs.known_topics)
    long_form = inputs.avg_response_length >= 120

    parts = _body(intent, topic, tone, long_form)
    for note in inputs.availability_notes[:1]:
        parts.append(f"Quick heads-up: {note.strip().rstrip('.')}.")

    body = " ".join(parts)
    greeting = _greeting(name, tone, gmail)
    if gmail:
        return f"{greeting}\n\n{body}\n\nBest regards"
    return f"{greeting} {body}"
