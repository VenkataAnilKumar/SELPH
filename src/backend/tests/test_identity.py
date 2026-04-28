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
