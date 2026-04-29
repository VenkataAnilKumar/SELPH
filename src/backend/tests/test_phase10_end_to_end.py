"""Phase 10 end-to-end API smoke tests."""

from datetime import datetime, UTC, timedelta

from app.models import Message


def _auth(client, email: str = "phase10@example.com") -> tuple[dict, str]:
    payload = {"email": email, "password": "TestPassword123", "name": "Phase 10"}
    signup = client.post("/v1/auth/signup", json=payload)
    assert signup.status_code == 201
    user_id = signup.json()["user"]["id"]
    token = signup.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}, user_id


class TestPhase10EndToEnd:
    def test_proactive_scan_and_preferences(self, client, test_db):
        headers, user_id = _auth(client, "proactive@example.com")

        msg = Message(
            user_id=user_id,
            channel="gmail",
            sender_id="contact_1",
            sender_name="Alex",
            content="Can we discuss a partnership deal?",
            created_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=20),
            channel_metadata={},
        )
        test_db.add(msg)
        test_db.commit()

        pref = client.get("/v1/proactive/preferences", headers=headers)
        assert pref.status_code == 200
        assert pref.json()["enabled"] is True

        scan = client.post("/v1/proactive/scan", headers=headers)
        assert scan.status_code == 200
        assert scan.json()["created"] >= 1

        items = client.get("/v1/proactive/suggestions", headers=headers)
        assert items.status_code == 200
        assert items.json()["total"] >= 1

    def test_crisis_activate_and_resolve(self, client):
        headers, _ = _auth(client, "crisis@example.com")

        activate = client.post(
            "/v1/twin/crisis/activate",
            headers=headers,
            json={"mode": "crisis_mode", "trigger_type": "manual"},
        )
        assert activate.status_code == 200
        assert activate.json()["mode"] == "crisis_mode"

        resolve = client.post("/v1/twin/crisis/resolve", headers=headers, json={"resolution_type": "manual_resume"})
        assert resolve.status_code == 200
        assert resolve.json()["mode"] == "normal"

    def test_multi_identity_profile_flow(self, client):
        headers, _ = _auth(client, "identityv2@example.com")

        created = client.post(
            "/v1/identity/profiles",
            headers=headers,
            json={"profile_name": "Creator", "profile_type": "creator", "vocabulary_description": "friendly"},
        )
        assert created.status_code == 201
        profile_id = created.json()["id"]

        listed = client.get("/v1/identity/profiles", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["total"] >= 1

        mapping = client.put(
            "/v1/identity/channel-mappings",
            headers=headers,
            json={"profile_id": profile_id, "channel": "instagram_dm", "platform_account": "acct_1", "priority": 1},
        )
        assert mapping.status_code == 200

    def test_style_checkpoint_flow(self, client):
        headers, _ = _auth(client, "style@example.com")

        refresh = client.post("/v1/twin/style/refresh", headers=headers)
        assert refresh.status_code == 200
        checkpoint_id = refresh.json()["checkpoint_id"]

        decide = client.post(
            f"/v1/twin/style/checkpoints/{checkpoint_id}/decide",
            headers=headers,
            json={"decision": "keep", "updated_dimensions": None},
        )
        assert decide.status_code == 200
        assert decide.json()["decision"] == "keep"

    def test_verification_endpoints(self, client):
        headers, _ = _auth(client, "verify@example.com")

        cert = client.get("/v1/twin/certificate", headers=headers)
        assert cert.status_code == 200
        twin_id = cert.json()["twin_public_id"]

        public_meta = client.get(f"/verify/{twin_id}")
        assert public_meta.status_code == 200

        check = client.get(f"/verify/{twin_id}/abc123")
        assert check.status_code == 200
        assert check.json()["valid"] is False

    def test_privacy_mode_flow(self, client):
        headers, _ = _auth(client, "privacy@example.com")

        cap = client.post("/v1/privacy/capability-check", headers=headers, json={"on_device_capable": True})
        assert cap.status_code == 200

        patch = client.patch("/v1/privacy/settings", headers=headers, json={"processing_mode": "on_device"})
        assert patch.status_code == 200
        assert patch.json()["processing_mode"] == "on_device"

    def test_t2t_session_flow(self, client):
        headers, _ = _auth(client, "t2t@example.com")

        create = client.post(
            "/v1/t2t/sessions?initiating_twin=twn_a",
            headers=headers,
            json={"receiving_twin": "twn_b", "session_type": "scheduling"},
        )
        assert create.status_code == 201
        session_id = create.json()["id"]

        approve_a = client.post(
            f"/v1/t2t/sessions/{session_id}/approve",
            headers=headers,
            json={"twin_id": "twn_a", "approved": True},
        )
        assert approve_a.status_code == 200

        approve_b = client.post(
            f"/v1/t2t/sessions/{session_id}/approve",
            headers=headers,
            json={"twin_id": "twn_b", "approved": True},
        )
        assert approve_b.status_code == 200
        assert approve_b.json()["status"] == "completed"
