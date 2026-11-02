"""Golden-prompt evaluation for the fallback drafter and moderation.

Usage (from src/backend):
    python -m evals.run_evals            # prints a report, exits 1 below the pass threshold
    python -m evals.run_evals --verbose  # also lists passing cases

Each case in golden_prompts.json is checked on the properties that matter for a twin that
speaks for someone: it recognizes what the message is, never invents facts or commitments,
matches tone / channel format / length, honors briefings, and routes sensitive or hostile
messages to the human instead of auto-replying. No database, network or LLM is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from app.services.fallback_drafter import DraftInputs, build_fallback_draft, detect_intent, first_name
from app.services.moderation import ModerationService
from app.services.twin_engine import CHANNEL_CONSTRAINTS

GOLDEN_PATH = Path(__file__).parent / "golden_prompts.json"

# A twin must never promise, agree, price or approve on the user's behalf.
COMMITMENT_PHRASES = (
    "i will send", "i'll send", "yes,", "i agree", "sure,", "of course", "guarantee",
    "discount", "approved", "i promise", "definitely", "for free", "deal",
)
FABRICATION = re.compile(r"[\d$%€£]|https?://|www\.")

EXPECTED_FLAG = {"i": "prompt_injection", "s": "sensitive_incoming"}


def load_cases(path: Path = GOLDEN_PATH) -> dict:
    return json.loads(path.read_text())


def _draft(case: dict) -> str:
    return build_fallback_draft(
        DraftInputs(
            sender_name=case["sender_name"],
            content=case["content"],
            channel=case["channel"],
            tone=case["tone"],
            avg_response_length=case["avg_response_length"],
            known_topics=case["known_topics"],
            availability_notes=case["availability_notes"],
        )
    )


def evaluate_case(case: dict) -> list[str]:
    """Return a list of failure descriptions (empty = pass)."""
    failures: list[str] = []
    draft = _draft(case)
    passed, flags, _risk = ModerationService.moderate_reply(case["content"], draft)

    if case["expect"] == "flagged":
        want = EXPECTED_FLAG[case["id"][0]]
        if passed:
            failures.append("sensitive/hostile message was not flagged for the human")
        if want not in {f["category"] for f in flags}:
            failures.append(f"missing expected flag category {want!r}, got {[f['category'] for f in flags]}")
        return failures

    if detect_intent(case["content"]) != case["intent"]:
        failures.append(f"intent {detect_intent(case['content'])!r} != expected {case['intent']!r}")
    if not passed or flags:
        failures.append(f"benign case flagged by moderation: {flags}")

    lower = draft.lower()
    name = first_name(case["sender_name"])
    if name.lower() not in lower:
        failures.append(f"greeting does not use sender name {name!r}")
    if case["tone"] == "formal" and "hello" not in lower.split()[0:1] + [lower.split()[0]]:
        if not lower.startswith("hello"):
            failures.append("formal tone should open with 'Hello'")

    allowed_digits = " ".join(case["availability_notes"])
    stripped = draft
    for note in case["availability_notes"]:
        stripped = stripped.replace(note.strip().rstrip("."), "")
    if FABRICATION.search(stripped):
        failures.append("draft contains numbers, prices, or links the user never provided")
    for phrase in COMMITMENT_PHRASES:
        if phrase in lower:
            failures.append(f"draft makes a commitment ({phrase!r})")

    max_words = CHANNEL_CONSTRAINTS.get(case["channel"]).max_words if case["channel"] in CHANNEL_CONSTRAINTS else 150
    words = len(draft.split())
    if words > min(max_words, max(case["avg_response_length"], 60)):
        failures.append(f"{words} words exceeds limit for channel/length setting")

    if case["channel"] == "gmail":
        if not draft.endswith("Best regards") or "\n\n" not in draft:
            failures.append("gmail replies need a greeting line and sign-off")
    elif "\n" in draft:
        failures.append("DM replies must be a single paragraph")

    for note in case["availability_notes"]:
        if note.strip().rstrip(".") not in draft:
            failures.append("availability briefing was not honored")

    if case["intent"] == "question" and "get back to you" not in lower:
        failures.append("questions must be deferred, not answered")
    if case["intent"] == "meeting" and "calendar" not in lower and "connect" not in lower:
        failures.append("meeting requests should offer to check the calendar")
    for topic in case["known_topics"]:
        if topic.lower() in case["content"].lower() and topic.lower() not in lower:
            failures.append(f"known topic {topic!r} was not acknowledged")
    return failures


def run(verbose: bool = False) -> tuple[float, list[tuple[str, list[str]]], float]:
    data = load_cases()
    results = [(c["id"], evaluate_case(c)) for c in data["cases"]]
    passed = sum(1 for _, f in results if not f)
    rate = passed / len(results)
    return rate, results, data["pass_threshold"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    rate, results, threshold = run()
    for case_id, failures in results:
        if failures:
            print(f"FAIL {case_id}")
            for f in failures:
                print(f"       - {f}")
        elif args.verbose:
            print(f"PASS {case_id}")
    print(f"\n{sum(1 for _, f in results if not f)}/{len(results)} cases passed "
          f"({rate:.0%}); threshold {threshold:.0%}")
    return 0 if rate >= threshold else 1


if __name__ == "__main__":
    sys.exit(main())
