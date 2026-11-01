"""Tests for the LLM-free fallback drafter."""

import pytest

from app.services.fallback_drafter import (
    DraftInputs,
    build_fallback_draft,
    detect_intent,
    first_name,
)


def _inputs(**kw):
    base = dict(
        sender_name="Priya Rao",
        content="hello",
        channel="instagram_dm",
        tone="friendly",
        avg_response_length=75,
        known_topics=[],
        availability_notes=[],
    )
    base.update(kw)
    return DraftInputs(**base)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("How do you stay ahead of AI news?", "question"),
        ("Loved your talk, thank you so much", "gratitude"),
        ("Love your talk! How do you prepare?", "question"),
        ("Can we schedule a call next week?", "meeting"),
        ("We'd like to sponsor your newsletter, what are your rates?", "business"),
        ("lol nice", "general"),
        ("Do you use Notion?", "question"),
    ],
)
def test_detect_intent(text, expected):
    assert detect_intent(text) == expected


def test_first_name_handles_missing_or_email_names():
    assert first_name("Priya Rao") == "Priya"
    assert first_name("") == "there"
    assert first_name("fan@example.com") == "there"


def test_question_does_not_fabricate_an_answer():
    draft = build_fallback_draft(_inputs(content="What tools do you use to build AI products?"))
    assert draft.startswith("Hey Priya!")
    assert "get back to you" in draft
    # never claims specific tools/facts
    assert "Claude" not in draft and "LangGraph" not in draft


def test_known_topic_is_acknowledged():
    draft = build_fallback_draft(
        _inputs(content="Any advice on agentic AI?", known_topics=["agentic ai"])
    )
    assert "agentic ai" in draft.lower()


def test_formal_tone_and_gmail_format():
    draft = build_fallback_draft(
        _inputs(channel="gmail", tone="formal", content="Could we schedule a call?")
    )
    assert draft.startswith("Hello Priya,\n\n")
    assert draft.endswith("Best regards")
    assert "calendar" in draft


def test_availability_briefing_is_included_once():
    draft = build_fallback_draft(
        _inputs(
            content="Quick question about pricing",
            availability_notes=["I'm at a conference this week", "second note ignored"],
        )
    )
    assert draft.count("Quick heads-up") == 1
    assert "conference" in draft
    assert "second note" not in draft


def test_longer_target_length_produces_longer_reply():
    short = build_fallback_draft(_inputs(content="How are you?", avg_response_length=60))
    long = build_fallback_draft(_inputs(content="How are you?", avg_response_length=200))
    assert len(long.split()) > len(short.split())


def test_drafts_differ_by_message_intent():
    a = build_fallback_draft(_inputs(content="Thanks so much, loved it"))
    b = build_fallback_draft(_inputs(content="Can we do a call?"))
    assert a != b
