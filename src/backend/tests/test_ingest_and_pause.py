"""Tests for the inline message-ingest endpoint and the one-tap pause guarantee."""

from unittest.mock import patch

from app.models import Draft


def _ingest(client, auth_headers, **overrides):
    body = {
        "channel": "instagram_dm",
        "sender_id": "fan_1",
        "sender_name": "Fan One",
        "content": "Loved your talk! Any tips for getting started?",
    }
    body.update(overrides)
    return client.post("/v1/messages/ingest", json=body, headers=auth_headers)


def _onboard(client, auth_headers):
    resp = client.post(
        "/v1/identity/onboard",
        headers=auth_headers,
        json={
            "role": "creator",
            "communication_style": "friendly",
            "topics_avoided": ["politics"],
            "response_length": "short",
            "audience_tone": "warm",
            "three_words": ["curious", "direct", "kind"],
        },
    )
    assert resp.status_code == 201, resp.text


@patch("app.tasks.draft_generation._safe_delay")
def test_ingest_creates_pending_draft(_mock_delay, client, auth_headers):
    _onboard(client, auth_headers)
    resp = _ingest(client, auth_headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["draft_id"]
    assert data["status"] == "draft_ready"

    pending = client.get("/v1/drafts/pending", headers=auth_headers).json()
    assert [d["id"] for d in pending] == [data["draft_id"]]


@patch("app.tasks.draft_generation._safe_delay")
def test_ingest_requires_auth(_mock_delay, client):
    resp = client.post(
        "/v1/messages/ingest",
        json={"sender_id": "x", "content": "hi"},
    )
    assert resp.status_code in (401, 403)


def test_ingest_validates_input(client, auth_headers):
    assert _ingest(client, auth_headers, content="").status_code == 422
    assert _ingest(client, auth_headers, content="x" * 10001).status_code == 422
    assert _ingest(client, auth_headers, sender_id="").status_code == 422


@patch("app.tasks.draft_generation._safe_delay")
def test_paused_twin_does_not_draft(_mock_delay, client, auth_headers, test_db):
    _onboard(client, auth_headers)
    assert client.post("/v1/twin/pause", headers=auth_headers).status_code == 200

    resp = _ingest(client, auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["draft_id"] is None
    assert data["routing_action"] == "skipped_manual_pause"
    assert test_db.query(Draft).count() == 0

    assert client.post("/v1/twin/resume", headers=auth_headers).status_code == 200
    assert _ingest(client, auth_headers, sender_id="fan_2").json()["draft_id"]


@patch("app.tasks.draft_generation._safe_delay")
def test_vip_sender_bypasses_twin(_mock_delay, client, auth_headers, test_db):
    _onboard(client, auth_headers)
    tier = client.put(
        "/v1/identity/sender-tiers",
        headers=auth_headers,
        json={"sender_id": "cofounder", "platform": "instagram_dm", "tier": 0},
    )
    assert tier.status_code == 200, tier.text

    data = _ingest(client, auth_headers, sender_id="cofounder").json()
    assert data["draft_id"] is None
    assert data["routing_action"] == "direct_notify"
    assert test_db.query(Draft).count() == 0
