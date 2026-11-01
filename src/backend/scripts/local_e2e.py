"""Local end-to-end walkthrough against a running SELPH API (no LLM key or channels needed).

Usage:
  python scripts/local_e2e.py [--base http://localhost:8000/v1]

Exercises: signup -> onboarding -> topics -> briefing -> VIP tier -> ingest -> approve/edit/reject
-> pause/resume -> stats. Exits non-zero on the first failed expectation.
"""

from __future__ import annotations

import argparse
import sys
import uuid

import httpx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000/v1")
    args = parser.parse_args()

    client = httpx.Client(base_url=args.base, timeout=30)
    failures: list[str] = []

    def check(label: str, resp: httpx.Response, expected: int | tuple[int, ...] = (200, 201)):
        ok_codes = (expected,) if isinstance(expected, int) else expected
        ok = resp.status_code in ok_codes
        print(f"{'PASS' if ok else 'FAIL'}  {label}  [{resp.status_code}]")
        if not ok:
            failures.append(f"{label}: {resp.status_code} {resp.text[:300]}")
        return resp.json() if ok and resp.content else {}

    email = f"e2e-{uuid.uuid4().hex[:8]}@example.com"
    signup = check(
        "signup",
        client.post("/auth/signup", json={"email": email, "password": "Str0ngPass!234", "name": "Maya"}),
    )
    if not signup:
        return 1
    client.headers["Authorization"] = f"Bearer {signup['tokens']['access_token']}"

    check("auth/me", client.get("/auth/me"))
    check(
        "identity/onboard",
        client.post(
            "/identity/onboard",
            json={
                "role": "AI creator and educator",
                "communication_style": "friendly",
                "topics_avoided": ["politics", "religion"],
                "response_length": "short",
                "audience_tone": "warm and encouraging",
                "three_words": ["curious", "direct", "kind"],
            },
        ),
    )
    check("topics/known", client.post("/identity/topics/known", json={"topic": "agentic AI"}))
    check(
        "briefing",
        client.post(
            "/identity/briefings",
            json={
                "briefing_type": "instruction",
                "topic": "conference week",
                "content": "I am at a conference this week. Keep replies short.",
                "priority": 8,
            },
        ),
    )
    check(
        "vip tier",
        client.put(
            "/identity/sender-tiers",
            json={"sender_id": "cofounder_1", "platform": "instagram_dm", "tier": 0, "tier_label": "Co-founder"},
        ),
    )

    # 1) normal fan message -> draft
    fan = check(
        "ingest fan message",
        client.post(
            "/messages/ingest",
            json={
                "channel": "instagram_dm",
                "sender_id": "fan_1",
                "sender_name": "Tech Girl",
                "content": "Your talk on agentic AI was great! How do you stay ahead without getting overwhelmed?",
            },
        ),
    )
    if fan.get("draft_id") is None:
        failures.append(f"fan message produced no draft: {fan}")
    else:
        draft = check("get draft", client.get(f"/drafts/{fan['draft_id']}"))
        print(f"      draft: {draft['content'][:120]!r} source={draft.get('generation_source')}")
        check("pending list", client.get("/drafts/pending"))
        check("approve", client.post(f"/drafts/{fan['draft_id']}/approve", json={"action": "approve"}))

    # 2) second message -> edit
    second = check(
        "ingest second message",
        client.post(
            "/messages/ingest",
            json={"channel": "instagram_dm", "sender_id": "fan_2", "content": "Can you recommend a good book on AI?"},
        ),
    )
    if second.get("draft_id"):
        edited = check(
            "edit draft",
            client.post(
                f"/drafts/{second['draft_id']}/approve",
                json={"action": "edit", "edited_content": "Try 'Co-Intelligence' by Ethan Mollick!"},
            ),
        )
        if edited and edited.get("status") != "edited":
            failures.append(f"edit status wrong: {edited.get('status')}")

    # 3) third -> reject
    third = check(
        "ingest third message",
        client.post(
            "/messages/ingest",
            json={"channel": "instagram_dm", "sender_id": "fan_3", "content": "Hi! Love your content."},
        ),
    )
    if third.get("draft_id"):
        check("reject draft", client.post(f"/drafts/{third['draft_id']}/approve", json={"action": "reject"}))

    # 3b) batch approval: similar questions are clustered and approved with one tap
    for i in range(3):
        check(
            f"ingest similar question {i + 1}",
            client.post(
                "/messages/ingest",
                json={
                    "channel": "instagram_dm",
                    "sender_id": f"batch_fan_{i}",
                    "sender_name": f"Fan {i}",
                    "content": "What tools do you use to build AI products?",
                },
            ),
        )
    clusters = check("cluster pending drafts", client.post("/drafts/batches/cluster", json={}))
    if not clusters.get("items"):
        failures.append("expected at least one batch cluster")
    else:
        cluster = clusters["items"][0]
        approved = check(
            "approve batch template",
            client.post(
                f"/drafts/batches/{cluster['id']}/approve",
                json={"template_approved": "Hey {sender_name}! I mostly use Claude Code and LangGraph."},
            ),
        )
        sends = check("batch sends", client.get(f"/drafts/batches/{cluster['id']}/sends"))
        if approved and sends.get("total", 0) < 2:
            failures.append(f"expected personalized sends per recipient, got {sends}")
        for row in sends.get("items", []):
            text = row.get("personalized_text", "")
            if "{" in text:
                failures.append(f"unresolved placeholder in batch send: {text!r}")

    # 3c) consent gates
    check("voice consent", client.post("/identity/voice/consent", json={"granted": True}))

    # 4) VIP bypasses the twin
    vip = check(
        "ingest VIP message",
        client.post(
            "/messages/ingest",
            json={
                "channel": "instagram_dm",
                "sender_id": "cofounder_1",
                "content": "Can we talk about the term sheet today?",
            },
        ),
    )
    if vip.get("draft_id") or vip.get("routing_action") != "direct_notify":
        failures.append(f"VIP message should bypass twin, got: {vip}")

    # 5) pause blocks drafting
    check("pause", client.post("/twin/pause"))
    paused = check(
        "ingest while paused",
        client.post(
            "/messages/ingest",
            json={"channel": "instagram_dm", "sender_id": "fan_4", "content": "Hello again!"},
        ),
    )
    if paused.get("draft_id"):
        failures.append(f"paused twin must not draft: {paused}")
    check("resume", client.post("/twin/resume"))

    check("twin stats", client.get("/twin/stats"))
    check("weekly digest", client.get("/twin/weekly-digest"))

    print()
    if failures:
        print(f"{len(failures)} failure(s):")
        for f in failures:
            print(" -", f)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
