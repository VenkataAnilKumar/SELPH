"""
Identity endpoint tests — Phase 1
POST /v1/identity/onboard
GET  /v1/identity/profile
PATCH /v1/identity/profile
GET  /v1/identity/topics/known
POST /v1/identity/topics/known
DELETE /v1/identity/topics/known/{topic}
GET  /v1/identity/topics/avoided
POST /v1/identity/topics/avoided
DELETE /v1/identity/topics/avoided/{topic}
GET  /v1/identity/confidence
"""

import pytest
from app.models import ChannelCredential, User

# ── Fixtures ──────────────────────────────────────────────────────────────────

ONBOARDING_PAYLOAD = {
    "role": "content creator",
    "communication_style": "casual",
    "topics_avoided": ["politics", "religion"],
    "response_length": "medium",
    "audience_tone": "warm and playful",
    "three_words": ["creative", "authentic", "energetic"],
}


# ── Onboarding ────────────────────────────────────────────────────────────────

class TestOnboarding:
    def test_onboarding_creates_twin_and_identity(self, client, auth_headers):
        """Successful onboarding returns twin_id and merged profile fields."""
        response = client.post(
            "/v1/identity/onboard",
            json=ONBOARDING_PAYLOAD,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["twin_id"]
        assert data["domain"] == "content creator"
        assert data["tone"] == "casual"
        assert data["avg_response_length"] == 150  # medium → 150
        assert data["vocabulary_description"] == "creative, authentic, energetic"
        assert "casual" in data["communication_style"]
        assert "politics" in data["topics_avoided"]
        assert "religion" in data["topics_avoided"]

    def test_onboarding_is_idempotent(self, client, auth_headers):
        """Calling onboard twice updates the profile without error."""
        client.post("/v1/identity/onboard", json=ONBOARDING_PAYLOAD, headers=auth_headers)

        updated = {**ONBOARDING_PAYLOAD, "role": "developer", "response_length": "detailed"}
        response = client.post("/v1/identity/onboard", json=updated, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["domain"] == "developer"
        assert data["avg_response_length"] == 300  # detailed → 300

    def test_onboarding_requires_exactly_three_words(self, client, auth_headers):
        """three_words with != 3 items returns 422."""
        bad = {**ONBOARDING_PAYLOAD, "three_words": ["only", "two"]}
        response = client.post("/v1/identity/onboard", json=bad, headers=auth_headers)
        assert response.status_code == 422

    def test_onboarding_invalid_communication_style(self, client, auth_headers):
        """Unrecognised communication_style returns 422."""
        bad = {**ONBOARDING_PAYLOAD, "communication_style": "sarcastic"}
        response = client.post("/v1/identity/onboard", json=bad, headers=auth_headers)
        assert response.status_code == 422

    def test_onboarding_invalid_response_length(self, client, auth_headers):
        """Unrecognised response_length returns 422."""
        bad = {**ONBOARDING_PAYLOAD, "response_length": "super_long"}
        response = client.post("/v1/identity/onboard", json=bad, headers=auth_headers)
        assert response.status_code == 422

    def test_onboarding_rejects_empty_topics_avoided(self, client, auth_headers):
        """topics_avoided must contain at least one non-empty topic."""
        bad = {**ONBOARDING_PAYLOAD, "topics_avoided": ["   ", ""]}
        response = client.post("/v1/identity/onboard", json=bad, headers=auth_headers)
        assert response.status_code == 422

    def test_onboarding_requires_auth(self, client):
        """Unauthenticated request returns 403 (middleware behaviour)."""
        response = client.post("/v1/identity/onboard", json=ONBOARDING_PAYLOAD)
        assert response.status_code == 403


# ── Profile ───────────────────────────────────────────────────────────────────

class TestIdentityProfile:
    def test_get_profile_before_onboarding(self, client, auth_headers):
        """Profile is empty (not complete) before onboarding."""
        response = client.get("/v1/identity/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["profile_complete"] is False
        assert data["topics_known"] == []
        assert data["topics_avoided"] == []

    def test_get_profile_after_onboarding(self, client, auth_headers):
        """Profile reflects onboarding data and is marked complete."""
        client.post("/v1/identity/onboard", json=ONBOARDING_PAYLOAD, headers=auth_headers)

        response = client.get("/v1/identity/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["profile_complete"] is True
        assert data["vocabulary_description"] == "creative, authentic, energetic"
        assert "politics" in data["topics_avoided"]

    def test_patch_profile_vocabulary(self, client, auth_headers):
        """PATCH only updates supplied fields."""
        client.post("/v1/identity/onboard", json=ONBOARDING_PAYLOAD, headers=auth_headers)

        response = client.patch(
            "/v1/identity/profile",
            json={"vocabulary_description": "bold, funny, sharp"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["vocabulary_description"] == "bold, funny, sharp"
        # communication_style unchanged from onboarding
        assert data["communication_style"] is not None

    def test_patch_profile_allows_clearing_vocabulary_with_empty_string(self, client, auth_headers):
        """Supplying an empty string should clear vocabulary_description."""
        client.post("/v1/identity/onboard", json=ONBOARDING_PAYLOAD, headers=auth_headers)

        response = client.patch(
            "/v1/identity/profile",
            json={"vocabulary_description": ""},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["vocabulary_description"] == ""

    def test_patch_profile_allows_clearing_topics_with_empty_list(self, client, auth_headers):
        """Supplying an empty list should clear known and avoided topics."""
        client.post("/v1/identity/onboard", json=ONBOARDING_PAYLOAD, headers=auth_headers)
        client.post("/v1/identity/topics/known", json={"topic": "photography"}, headers=auth_headers)

        response = client.patch(
            "/v1/identity/profile",
            json={"topics_known": [], "topics_avoided": []},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["topics_known"] == []
        assert data["topics_avoided"] == []

    def test_patch_profile_requires_auth(self, client):
        """Unauthenticated PATCH returns 403 (middleware behaviour)."""
        response = client.patch("/v1/identity/profile", json={"vocabulary_description": "x"})
        assert response.status_code == 403


# ── Topics: Known ─────────────────────────────────────────────────────────────

class TestKnownTopics:
    def test_add_known_topic(self, client, auth_headers):
        """Adding a known topic returns the new topic."""
        response = client.post(
            "/v1/identity/topics/known",
            json={"topic": "photography", "context": "landscape and street"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == "photography"
        assert data["topic_type"] == "known"
        assert data["context"] == "landscape and street"

    def test_list_known_topics(self, client, auth_headers):
        """Known topics list includes added topics."""
        client.post("/v1/identity/topics/known", json={"topic": "fitness"}, headers=auth_headers)
        client.post("/v1/identity/topics/known", json={"topic": "travel"}, headers=auth_headers)

        response = client.get("/v1/identity/topics/known", headers=auth_headers)
        assert response.status_code == 200
        topics = response.json()
        assert "fitness" in topics
        assert "travel" in topics

    def test_add_duplicate_known_topic_increments_frequency(self, client, auth_headers):
        """Adding the same known topic twice increments frequency, not duplicates."""
        client.post("/v1/identity/topics/known", json={"topic": "gaming"}, headers=auth_headers)
        response = client.post(
            "/v1/identity/topics/known", json={"topic": "gaming"}, headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["frequency"] == 2

    def test_delete_known_topic(self, client, auth_headers):
        """Deleting a known topic removes it from the list."""
        client.post("/v1/identity/topics/known", json={"topic": "cooking"}, headers=auth_headers)
        del_response = client.delete("/v1/identity/topics/known/cooking", headers=auth_headers)
        assert del_response.status_code == 204

        topics = client.get("/v1/identity/topics/known", headers=auth_headers).json()
        assert "cooking" not in topics

    def test_delete_nonexistent_known_topic_returns_404(self, client, auth_headers):
        """Deleting a topic that doesn't exist returns 404."""
        response = client.delete("/v1/identity/topics/known/nonexistent", headers=auth_headers)
        assert response.status_code == 404


# ── Topics: Avoided ───────────────────────────────────────────────────────────

class TestAvoidedTopics:
    def test_add_avoided_topic(self, client, auth_headers):
        """Adding an avoided topic returns the new topic."""
        response = client.post(
            "/v1/identity/topics/avoided",
            json={"topic": "politics", "context": "too divisive"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == "politics"
        assert data["topic_type"] == "avoided"

    def test_list_avoided_topics(self, client, auth_headers):
        """Avoided topics list includes added topics."""
        client.post("/v1/identity/topics/avoided", json={"topic": "finance"}, headers=auth_headers)
        response = client.get("/v1/identity/topics/avoided", headers=auth_headers)
        assert response.status_code == 200
        assert "finance" in response.json()

    def test_delete_avoided_topic(self, client, auth_headers):
        """Deleting an avoided topic removes it from the list."""
        client.post("/v1/identity/topics/avoided", json={"topic": "religion"}, headers=auth_headers)
        client.delete("/v1/identity/topics/avoided/religion", headers=auth_headers)
        topics = client.get("/v1/identity/topics/avoided", headers=auth_headers).json()
        assert "religion" not in topics

    def test_delete_nonexistent_avoided_topic_returns_404(self, client, auth_headers):
        """Deleting a topic that doesn't exist returns 404."""
        response = client.delete("/v1/identity/topics/avoided/ghost", headers=auth_headers)
        assert response.status_code == 404

    def test_known_and_avoided_topics_are_independent(self, client, auth_headers):
        """A topic can exist as both known and avoided independently."""
        client.post("/v1/identity/topics/known", json={"topic": "health"}, headers=auth_headers)
        client.post("/v1/identity/topics/avoided", json={"topic": "health"}, headers=auth_headers)

        known = client.get("/v1/identity/topics/known", headers=auth_headers).json()
        avoided = client.get("/v1/identity/topics/avoided", headers=auth_headers).json()
        assert "health" in known
        assert "health" in avoided


# ── Confidence ────────────────────────────────────────────────────────────────

class TestConfidence:
    def test_confidence_low_before_onboarding(self, client, auth_headers):
        """Confidence is low (0.0) before any profile data."""
        response = client.get("/v1/identity/confidence", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 0.0
        assert data["label"] == "low"
        assert data["fields_complete"] == 0
        assert data["total_fields"] == 4

    def test_confidence_high_after_onboarding_with_topics(self, client, auth_headers):
        """Confidence is high once onboarding is complete and topics are added."""
        client.post("/v1/identity/onboard", json=ONBOARDING_PAYLOAD, headers=auth_headers)
        client.post("/v1/identity/topics/known", json={"topic": "photography"}, headers=auth_headers)

        response = client.get("/v1/identity/confidence", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # vocabulary_description + communication_style + topics_avoided = 3 fields
        # topics_known = 1 more → 4/4 = 1.0 high
        assert data["score"] == 1.0
        assert data["label"] == "high"

    def test_confidence_requires_auth(self, client):
        """Unauthenticated request returns 403 (middleware behaviour)."""
        response = client.get("/v1/identity/confidence")
        assert response.status_code == 403


class TestOnboardingStatus:
    def test_onboarding_status_before_onboarding(self, client, auth_headers):
        response = client.get("/v1/identity/onboarding/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_complete"] is False
        assert data["profile_complete"] is False
        assert data["completion_percent"] == 33
        assert "complete_onboarding" in data["blockers"]
        assert "connect_first_channel" in data["blockers"]

    def test_onboarding_status_after_onboarding_and_channel_connect(
        self,
        client,
        auth_headers,
        test_db,
        test_user_data,
    ):
        client.post("/v1/identity/onboard", json=ONBOARDING_PAYLOAD, headers=auth_headers)

        user = test_db.query(User).filter(User.email == test_user_data["email"]).first()
        credential = ChannelCredential(
            user_id=user.id,
            channel="instagram",
            credential_type="oauth_token",
            credential_value="token-123",
            is_active=True,
        )
        test_db.add(credential)
        test_db.commit()

        response = client.get("/v1/identity/onboarding/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_complete"] is True
        assert data["profile_complete"] is True
        assert data["completion_percent"] == 100
        assert "instagram" in data["connected_channels"]
        assert "gmail" in data["missing_channels"]
        assert data["blockers"] == []

    def test_onboarding_status_requires_auth(self, client):
        response = client.get("/v1/identity/onboarding/status")
        assert response.status_code == 403


# ── Voice Clone (Phase 6 PR B) ─────────────────────────────────────────────

class TestVoiceCloneEnrollment:
    def test_voice_consent_defaults_to_false(self, client, auth_headers):
        response = client.get("/v1/identity/voice/consent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["consent_type"] == "voice_clone"
        assert data["granted"] is False

    def test_grant_and_revoke_voice_consent(self, client, auth_headers):
        grant = client.post(
            "/v1/identity/voice/consent",
            json={"granted": True},
            headers=auth_headers,
        )
        assert grant.status_code == 200
        assert grant.json()["granted"] is True
        assert grant.json()["granted_at"] is not None

        revoke = client.post(
            "/v1/identity/voice/consent",
            json={"granted": False},
            headers=auth_headers,
        )
        assert revoke.status_code == 200
        assert revoke.json()["granted"] is False

    def test_enroll_requires_consent(self, client, auth_headers):
        response = client.post(
            "/v1/identity/voice/enroll",
            json={
                "voice_provider": "mock",
                "voice_model_id": "voice-001",
                "voice_sample_url": "https://example.com/sample.wav",
            },
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_enroll_after_consent_and_fetch_profile(self, client, auth_headers):
        client.post(
            "/v1/identity/voice/consent",
            json={"granted": True},
            headers=auth_headers,
        )

        enroll = client.post(
            "/v1/identity/voice/enroll",
            json={
                "voice_provider": "mock",
                "voice_model_id": "voice-001",
                "voice_sample_url": "https://example.com/sample.wav",
            },
            headers=auth_headers,
        )
        assert enroll.status_code == 200
        data = enroll.json()
        assert data["enrolled"] is True
        assert data["voice_provider"] == "mock"
        assert data["voice_model_id"] == "voice-001"
        assert data["consent_granted"] is True

        profile = client.get("/v1/identity/voice/profile", headers=auth_headers)
        assert profile.status_code == 200
        profile_data = profile.json()
        assert profile_data["enrolled"] is True
        assert profile_data["voice_model_id"] == "voice-001"

    def test_clear_voice_profile(self, client, auth_headers):
        client.post("/v1/identity/voice/consent", json={"granted": True}, headers=auth_headers)
        client.post(
            "/v1/identity/voice/enroll",
            json={"voice_provider": "mock", "voice_model_id": "voice-123"},
            headers=auth_headers,
        )

        clear = client.delete("/v1/identity/voice/profile", headers=auth_headers)
        assert clear.status_code == 200
        assert clear.json()["enrolled"] is False
        assert clear.json()["voice_model_id"] is None

    def test_revoke_consent_clears_voice_profile(self, client, auth_headers):
        client.post("/v1/identity/voice/consent", json={"granted": True}, headers=auth_headers)
        client.post(
            "/v1/identity/voice/enroll",
            json={"voice_provider": "mock", "voice_model_id": "voice-xyz"},
            headers=auth_headers,
        )

        client.post("/v1/identity/voice/consent", json={"granted": False}, headers=auth_headers)
        profile = client.get("/v1/identity/voice/profile", headers=auth_headers)
        assert profile.status_code == 200
        assert profile.json()["enrolled"] is False
        assert profile.json()["voice_model_id"] is None

    def test_voice_endpoints_require_auth(self, client):
        assert client.get("/v1/identity/voice/consent").status_code == 403
        assert client.post("/v1/identity/voice/consent", json={"granted": True}).status_code == 403
        assert client.post("/v1/identity/voice/enroll", json={"voice_provider": "mock"}).status_code == 403
        assert client.get("/v1/identity/voice/profile").status_code == 403
        assert client.delete("/v1/identity/voice/profile").status_code == 403


# ── Avatar Clone (Phase 7 PR B) ─────────────────────────────────────────────

class TestAvatarCloneEnrollment:
    def test_avatar_consent_defaults_to_false(self, client, auth_headers):
        response = client.get("/v1/identity/avatar/consent", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["consent_type"] == "avatar_clone"
        assert data["granted"] is False

    def test_grant_and_revoke_avatar_consent(self, client, auth_headers):
        grant = client.post(
            "/v1/identity/avatar/consent",
            json={"granted": True},
            headers=auth_headers,
        )
        assert grant.status_code == 200
        assert grant.json()["granted"] is True
        assert grant.json()["granted_at"] is not None

        revoke = client.post(
            "/v1/identity/avatar/consent",
            json={"granted": False},
            headers=auth_headers,
        )
        assert revoke.status_code == 200
        assert revoke.json()["granted"] is False

    def test_enroll_requires_consent(self, client, auth_headers):
        response = client.post(
            "/v1/identity/avatar/enroll",
            json={
                "avatar_provider": "mock",
                "avatar_model_id": "avatar-001",
                "avatar_sample_url": "https://example.com/sample.mp4",
            },
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_enroll_after_consent_and_fetch_profile(self, client, auth_headers):
        client.post(
            "/v1/identity/avatar/consent",
            json={"granted": True},
            headers=auth_headers,
        )

        enroll = client.post(
            "/v1/identity/avatar/enroll",
            json={
                "avatar_provider": "mock",
                "avatar_model_id": "avatar-001",
                "avatar_sample_url": "https://example.com/sample.mp4",
            },
            headers=auth_headers,
        )
        assert enroll.status_code == 200
        data = enroll.json()
        assert data["enrolled"] is True
        assert data["avatar_provider"] == "mock"
        assert data["avatar_model_id"] == "avatar-001"
        assert data["consent_granted"] is True

        profile = client.get("/v1/identity/avatar/profile", headers=auth_headers)
        assert profile.status_code == 200
        profile_data = profile.json()
        assert profile_data["enrolled"] is True
        assert profile_data["avatar_model_id"] == "avatar-001"

    def test_clear_avatar_profile(self, client, auth_headers):
        client.post("/v1/identity/avatar/consent", json={"granted": True}, headers=auth_headers)
        client.post(
            "/v1/identity/avatar/enroll",
            json={"avatar_provider": "mock", "avatar_model_id": "avatar-123"},
            headers=auth_headers,
        )

        clear = client.delete("/v1/identity/avatar/profile", headers=auth_headers)
        assert clear.status_code == 200
        assert clear.json()["enrolled"] is False
        assert clear.json()["avatar_model_id"] is None

    def test_revoke_consent_clears_avatar_profile(self, client, auth_headers):
        client.post("/v1/identity/avatar/consent", json={"granted": True}, headers=auth_headers)
        client.post(
            "/v1/identity/avatar/enroll",
            json={"avatar_provider": "mock", "avatar_model_id": "avatar-xyz"},
            headers=auth_headers,
        )

        client.post("/v1/identity/avatar/consent", json={"granted": False}, headers=auth_headers)
        profile = client.get("/v1/identity/avatar/profile", headers=auth_headers)
        assert profile.status_code == 200
        assert profile.json()["enrolled"] is False
        assert profile.json()["avatar_model_id"] is None

    def test_avatar_endpoints_require_auth(self, client):
        assert client.get("/v1/identity/avatar/consent").status_code == 403
        assert client.post("/v1/identity/avatar/consent", json={"granted": True}).status_code == 403
        assert client.post("/v1/identity/avatar/enroll", json={"avatar_provider": "mock"}).status_code == 403
        assert client.get("/v1/identity/avatar/profile").status_code == 403
        assert client.delete("/v1/identity/avatar/profile").status_code == 403


# ── Twin Briefings (Phase 9 PR A) ───────────────────────────────────────────

class TestTwinBriefings:
    def test_create_and_list_active_briefings(self, client, auth_headers):
        create = client.post(
            "/v1/identity/briefings",
            json={
                "briefing_type": "fact",
                "topic": "new course launch",
                "content": "My new course is live this week at selph.ai/course",
                "priority": 8,
            },
            headers=auth_headers,
        )
        assert create.status_code == 201
        created = create.json()
        assert created["briefing_type"] == "fact"
        assert created["topic"] == "new course launch"
        assert created["priority"] == 8
        assert created["is_active"] is True

        listed = client.get("/v1/identity/briefings", headers=auth_headers)
        assert listed.status_code == 200
        payload = listed.json()
        assert payload["active_count"] == 1
        assert len(payload["items"]) == 1
        assert payload["items"][0]["topic"] == "new course launch"

    def test_clear_briefing_and_include_inactive(self, client, auth_headers):
        create = client.post(
            "/v1/identity/briefings",
            json={
                "briefing_type": "instruction",
                "topic": "collabs",
                "content": "Ask collab requests to DM my manager",
                "priority": 7,
            },
            headers=auth_headers,
        )
        briefing_id = create.json()["id"]

        clear = client.post(f"/v1/identity/briefings/{briefing_id}/clear", headers=auth_headers)
        assert clear.status_code == 200
        cleared = clear.json()
        assert cleared["is_active"] is False
        assert cleared["cleared_at"] is not None

        active_only = client.get("/v1/identity/briefings", headers=auth_headers)
        assert active_only.status_code == 200
        assert active_only.json()["active_count"] == 0
        assert active_only.json()["items"] == []

        include_inactive = client.get("/v1/identity/briefings?include_inactive=true", headers=auth_headers)
        assert include_inactive.status_code == 200
        assert len(include_inactive.json()["items"]) == 1
        assert include_inactive.json()["items"][0]["is_active"] is False

    def test_create_briefing_enforces_max_10_active(self, client, auth_headers):
        for idx in range(10):
            response = client.post(
                "/v1/identity/briefings",
                json={
                    "briefing_type": "fact",
                    "topic": f"topic-{idx}",
                    "content": f"briefing content {idx}",
                    "priority": 5,
                },
                headers=auth_headers,
            )
            assert response.status_code == 201

        blocked = client.post(
            "/v1/identity/briefings",
            json={
                "briefing_type": "fact",
                "topic": "overflow",
                "content": "this should fail",
                "priority": 5,
            },
            headers=auth_headers,
        )
        assert blocked.status_code == 400
        assert "Maximum 10 active briefings" in blocked.json()["detail"]

    def test_briefing_endpoints_require_auth(self, client):
        assert client.get("/v1/identity/briefings").status_code == 403
        assert client.post(
            "/v1/identity/briefings",
            json={
                "briefing_type": "fact",
                "topic": "x",
                "content": "y",
                "priority": 5,
            },
        ).status_code == 403
