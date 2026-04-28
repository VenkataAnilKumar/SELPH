"""
Integration tests for backend API endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.models import AuditLog, Draft
from app.models.user import User
from app.services.draft import DraftService
from app.services.message import MessageService


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_signup_success(self, client, test_user_data):
        """Test successful signup"""
        response = client.post("/v1/auth/signup", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]

    def test_signup_missing_email(self, client):
        """Test signup with missing email"""
        response = client.post("/v1/auth/signup", json={"password": "TestPassword123", "name": "Test"})
        
        assert response.status_code == 422

    def test_signup_missing_password(self, client):
        """Test signup with missing password"""
        response = client.post("/v1/auth/signup", json={"email": "test@example.com", "name": "Test"})
        
        assert response.status_code == 422

    def test_signup_invalid_email(self, client):
        """Test signup with invalid email"""
        response = client.post(
            "/v1/auth/signup", json={"email": "invalid", "password": "TestPassword123", "name": "Test"}
        )
        
        assert response.status_code == 422

    def test_signup_duplicate_email(self, client, test_user_data):
        """Test signup with duplicate email"""
        # First signup
        client.post("/v1/auth/signup", json=test_user_data)
        
        # Second signup with same email
        response = client.post("/v1/auth/signup", json=test_user_data)
        
        assert response.status_code == 400

    def test_login_success(self, client, test_user_data):
        """Test successful login"""
        # Signup first
        client.post("/v1/auth/signup", json=test_user_data)
        
        # Login
        response = client.post(
            "/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tokens" in data
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
        assert "user" in data

    def test_login_invalid_email(self, client):
        """Test login with invalid email"""
        response = client.post(
            "/v1/auth/login", json={"email": "wrong@example.com", "password": "WrongPassword123"}
        )
        
        assert response.status_code == 401

    def test_login_invalid_password(self, client, test_user_data):
        """Test login with invalid password"""
        # Signup first
        client.post("/v1/auth/signup", json=test_user_data)
        
        # Login with wrong password
        response = client.post(
            "/v1/auth/login",
            json={"email": test_user_data["email"], "password": "WrongPassword123"},
        )
        
        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user"""
        response = client.get("/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data

    def test_logout(self, client, auth_headers):
        """Test logout"""
        response = client.post("/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200

    def test_refresh_token(self, client, test_user_data):
        """Test token refresh"""
        # Signup
        client.post("/v1/auth/signup", json=test_user_data)

        # Login and get access token
        login_response = client.post(
            "/v1/auth/login",
            json={"email": test_user_data["email"], "password": test_user_data["password"]},
        )
        access_token = login_response.json()["tokens"]["access_token"]
        
        # Refresh requires authenticated user context
        response = client.post("/v1/auth/refresh", headers={"Authorization": f"Bearer {access_token}"})
        
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestTwinEndpoints:
    """Test twin endpoints"""

    def test_get_twin(self, client, auth_headers):
        """Test getting twin profile"""
        response = client.get("/v1/twin/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "user_id" in data
        assert "status" in data
        assert data["status"] == "active"

    def test_pause_twin(self, client, auth_headers):
        """Test pausing twin"""
        response = client.post("/v1/twin/pause", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"

    def test_resume_twin(self, client, auth_headers):
        """Test resuming twin"""
        # Pause first
        client.post("/v1/twin/pause", headers=auth_headers)
        
        # Resume
        response = client.post("/v1/twin/resume", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"

    def test_get_twin_stats(self, client, auth_headers):
        """Test getting twin statistics"""
        response = client.get("/v1/twin/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "domain" in data
        assert "tone" in data
        assert "total_messages" in data
        assert "pending_drafts" in data
        assert "total_estimated_tokens" in data
        assert "total_estimated_cost_usd" in data
        assert "fallback_rate" in data
        assert "generation_source_breakdown" in data
        assert "model_breakdown" in data
        assert "fallback_reason_breakdown" in data

    def test_update_twin_profile(self, client, auth_headers, test_twin_data):
        """Test updating twin profile"""
        response = client.put(
            "/v1/twin/me", headers=auth_headers, json=test_twin_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["domain"] == test_twin_data["domain"]
        assert data["tone"] == test_twin_data["tone"]

    def test_get_twin_unauthorized(self, client):
        """Test getting twin without auth"""
        response = client.get("/v1/twin/me")
        
        assert response.status_code == 403


class TestMessageEndpoints:
    """Test message endpoints"""

    def test_get_messages(self, client, auth_headers, test_message_data):
        """Test getting user's messages"""
        response = client.get("/v1/messages", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_messages_with_limit(self, client, auth_headers):
        """Test getting messages with limit"""
        response = client.get("/v1/messages?limit=5", headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_messages_with_status_filter(self, client, auth_headers):
        """Test getting messages with status filter"""
        response = client.get("/v1/messages?status=received", headers=auth_headers)
        
        assert response.status_code == 200

    def test_get_messages_unauthorized(self, client):
        """Test getting messages without auth"""
        response = client.get("/v1/messages")
        
        assert response.status_code == 403


class TestDraftEndpoints:
    """Test draft endpoints"""

    @staticmethod
    def _get_authenticated_user(test_db, test_user_data):
        return test_db.query(User).filter(User.email == test_user_data["email"]).first()

    @staticmethod
    def _seed_draft(test_db, test_user, **overrides):
        message = MessageService.create_message(
            test_db,
            test_user.id,
            "instagram_dm",
            overrides.pop("sender_id", "sender_seed"),
            overrides.pop("sender_name", "Seed Sender"),
            overrides.pop("content", "Hello from seed"),
            {},
        )
        return DraftService.create_draft(
            test_db,
            message.id,
            test_user.id,
            test_user.twin.id,
            overrides.pop("draft_content", "Seed draft reply"),
            confidence_score=overrides.pop("confidence_score", 0.82),
            confidence_label=overrides.pop("confidence_label", "High"),
            confidence_reasoning=overrides.pop("confidence_reasoning", "Seeded for endpoint tests"),
            moderation_passed=overrides.pop("moderation_passed", True),
            moderation_flags=overrides.pop("moderation_flags", []),
            generation_source=overrides.pop("generation_source", "llm"),
            llm_model=overrides.pop("llm_model", "claude-sonnet-4-6"),
            fallback_reason=overrides.pop("fallback_reason", None),
            llm_calls=overrides.pop("llm_calls", 1),
            parse_retry_count=overrides.pop("parse_retry_count", 0),
            llm_latency_ms=overrides.pop("llm_latency_ms", 250),
            pipeline_latency_ms=overrides.pop("pipeline_latency_ms", 400),
            estimated_input_tokens=overrides.pop("estimated_input_tokens", 120),
            estimated_output_tokens=overrides.pop("estimated_output_tokens", 40),
            estimated_total_tokens=overrides.pop("estimated_total_tokens", 160),
            estimated_cost_usd=overrides.pop("estimated_cost_usd", 0.00096),
        )

    def test_get_pending_drafts(self, client, auth_headers):
        """Test getting pending drafts"""
        response = client.get("/v1/drafts/pending", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_draft_returns_generation_metadata(self, client, auth_headers, test_db, test_user_data):
        """Draft detail endpoint should return persisted generation/cost metadata."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user, fallback_reason="llm_disabled", generation_source="deterministic")

        response = client.get(f"/v1/drafts/{draft.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["generation_source"] == "deterministic"
        assert data["llm_model"] == "claude-sonnet-4-6"
        assert data["fallback_reason"] == "llm_disabled"
        assert data["estimated_total_tokens"] == 160
        assert data["estimated_cost_usd"] == 0.00096

    def test_pending_drafts_returns_generation_metadata(self, client, auth_headers, test_db, test_user_data):
        """Pending drafts list should expose generation/cost metadata for dashboard use."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        self._seed_draft(test_db, current_user, generation_source="llm")

        response = client.get("/v1/drafts/pending", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["generation_source"] == "llm"
        assert data[0]["estimated_total_tokens"] == 160

    def test_approve_draft_updates_status_and_audit(self, client, auth_headers, test_db, test_user_data):
        """Approve action should update status and create audit details with cost metadata."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)

        response = client.post(
            f"/v1/drafts/{draft.id}/approve",
            headers=auth_headers,
            json={"action": "approve"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

        audit = test_db.query(AuditLog).filter(AuditLog.resource_id == draft.id, AuditLog.action == "approve_draft").first()
        assert audit is not None
        assert audit.details["generation_source"] == "llm"
        assert audit.details["estimated_total_tokens"] == 160

    def test_edit_draft_requires_content_and_marks_edited(self, client, auth_headers, test_db, test_user_data):
        """Edit action should require content and persist edited status once supplied."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)

        missing = client.post(
            f"/v1/drafts/{draft.id}/approve",
            headers=auth_headers,
            json={"action": "edit"},
        )
        assert missing.status_code == 400

        response = client.post(
            f"/v1/drafts/{draft.id}/approve",
            headers=auth_headers,
            json={"action": "edit", "edited_content": "Human-approved rewrite"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "edited"

    def test_reject_and_skip_draft_follow_state_machine(self, client, auth_headers, test_db, test_user_data):
        """Reject and skip should close the draft and block re-processing."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        reject_draft = self._seed_draft(test_db, current_user, sender_id="reject_sender")
        skip_draft = self._seed_draft(test_db, current_user, sender_id="skip_sender")

        reject_response = client.post(
            f"/v1/drafts/{reject_draft.id}/approve",
            headers=auth_headers,
            json={"action": "reject"},
        )
        assert reject_response.status_code == 200
        assert reject_response.json()["status"] == "rejected"

        skip_response = client.post(
            f"/v1/drafts/{skip_draft.id}/approve",
            headers=auth_headers,
            json={"action": "skip"},
        )
        assert skip_response.status_code == 200
        assert skip_response.json()["status"] == "rejected"

        second_attempt = client.post(
            f"/v1/drafts/{skip_draft.id}/approve",
            headers=auth_headers,
            json={"action": "approve"},
        )
        assert second_attempt.status_code == 400

    def test_twin_stats_breaks_down_generation_sources_and_models(self, client, auth_headers, test_db, test_user_data):
        """Twin stats should expose dashboard-friendly breakdowns."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        self._seed_draft(test_db, current_user, generation_source="llm", llm_model="claude-sonnet-4-6", estimated_total_tokens=200, estimated_cost_usd=0.001)
        deterministic = self._seed_draft(
            test_db,
            current_user,
            sender_id="fallback_sender",
            generation_source="deterministic",
            llm_model="deterministic-fallback",
            fallback_reason="llm_disabled",
            estimated_total_tokens=80,
            estimated_cost_usd=0.0,
        )
        deterministic.status = "edited"
        test_db.commit()

        response = client.get("/v1/twin/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["processed_drafts"] == 1
        assert data["total_estimated_tokens"] == 280
        assert data["total_estimated_cost_usd"] == 0.001
        assert data["generation_source_breakdown"]["llm"] == 1
        assert data["generation_source_breakdown"]["deterministic"] == 1
        assert data["model_breakdown"]["claude-sonnet-4-6"] == 1
        assert data["model_breakdown"]["deterministic-fallback"] == 1
        assert data["fallback_reason_breakdown"]["llm_disabled"] == 1

    def test_approve_draft(self, client, auth_headers):
        """Test approving a draft"""
        # This test would require creating a draft first
        # For now, test endpoint exists and requires auth
        response = client.post(
            "/v1/drafts/1/approve",
            headers=auth_headers,
            json={"action": "approve"},
        )
        
        # May be 404 if draft doesn't exist, but shouldn't be 403
        assert response.status_code != 403

    def test_reject_draft(self, client, auth_headers):
        """Test rejecting a draft"""
        response = client.post(
            "/v1/drafts/1/approve",
            headers=auth_headers,
            json={"action": "reject"},
        )
        
        assert response.status_code != 403

    def test_edit_draft(self, client, auth_headers):
        """Test editing a draft"""
        response = client.post(
            "/v1/drafts/1/approve",
            headers=auth_headers,
            json={"action": "edit", "edited_content": "Updated response"},
        )
        
        assert response.status_code != 403

    def test_draft_unauthorized(self, client):
        """Test draft endpoints without auth"""
        response = client.get("/v1/drafts/pending")
        
        assert response.status_code == 403


class TestPushTokenEndpoints:
    """Tests for device push-token registration"""

    def test_register_push_token_stores_token(self, client, test_db, auth_headers, test_user_data):
        """POST /v1/auth/push-token stores the token on the user record."""
        from app.models.user import User

        response = client.post(
            "/v1/auth/push-token",
            json={"token": "ExponentPushToken[abc123]"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["registered"] is True

        user = test_db.query(User).filter(User.email == test_user_data["email"]).first()
        assert user is not None
        assert user.push_token == "ExponentPushToken[abc123]"

    def test_register_push_token_updates_existing_token(self, client, test_db, auth_headers, test_user_data):
        """Re-registering with a new token overwrites the old value."""
        from app.models.user import User

        client.post(
            "/v1/auth/push-token",
            json={"token": "ExponentPushToken[old]"},
            headers=auth_headers,
        )
        client.post(
            "/v1/auth/push-token",
            json={"token": "ExponentPushToken[new]"},
            headers=auth_headers,
        )

        user = test_db.query(User).filter(User.email == test_user_data["email"]).first()
        assert user.push_token == "ExponentPushToken[new]"

    def test_register_push_token_requires_auth(self, client):
        """Unauthenticated requests are rejected with 403."""
        response = client.post(
            "/v1/auth/push-token",
            json={"token": "ExponentPushToken[abc123]"},
        )
        assert response.status_code == 403


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "ok"]
