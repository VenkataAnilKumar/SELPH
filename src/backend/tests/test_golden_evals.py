"""Golden-prompt gate: the drafter + moderation must pass >= 95% of the 50 golden cases."""

import json

from evals import run_evals
from evals.run_evals import evaluate_case, load_cases, run


def test_golden_suite_has_50_unique_cases():
    cases = load_cases()["cases"]
    assert len(cases) >= 50
    assert len({c["id"] for c in cases}) == len(cases)


def test_golden_pass_rate_meets_threshold():
    rate, results, threshold = run()
    failing = {cid: f for cid, f in results if f}
    assert rate >= threshold, f"golden pass rate {rate:.0%} < {threshold:.0%}: {json.dumps(failing, indent=1)}"


def test_every_golden_case_passes():
    """Stricter than the threshold: today the suite is clean, so any regression is visible."""
    failing = {cid: f for cid, f in run()[1] if f}
    assert not failing, json.dumps(failing, indent=1)


def test_eval_gate_actually_catches_bad_drafts(monkeypatch):
    """Prove the gate can fail: a drafter that promises discounts and invents prices must not pass."""
    case = next(c for c in load_cases()["cases"] if c["id"] == "b01")
    assert evaluate_case(case) == []

    monkeypatch.setattr(run_evals, "build_fallback_draft", lambda _inputs: "Yes, of course! I'll send $500 and a 50% discount.")
    failures = evaluate_case(case)
    assert any("commitment" in f for f in failures)
    assert any("numbers, prices" in f for f in failures)
    assert any("greeting does not use sender name" in f for f in failures)


def test_eval_gate_requires_flagging_hostile_messages(monkeypatch):
    case = next(c for c in load_cases()["cases"] if c["id"] == "i01")
    assert evaluate_case(case) == []

    monkeypatch.setattr(run_evals.ModerationService, "moderate_reply", staticmethod(lambda a, b: (True, [], 0.0)))
    assert any("not flagged" in f for f in evaluate_case(case))
