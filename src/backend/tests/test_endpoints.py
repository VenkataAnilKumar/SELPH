"""
Integration tests for backend API endpoints
"""

import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
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

    @staticmethod
    def _seed_quality_draft(
        test_db,
        user,
        *,
        status: str,
        latency: int = 400,
        channel: str = "instagram_dm",
    ):
        message = MessageService.create_message(
            test_db,
            user.id,
            channel,
            f"sender-{status}-{latency}",
            "Quality Sender",
            "Quality check message",
            {},
        )
        draft = DraftService.create_draft(
            test_db,
            message.id,
            user.id,
            user.twin.id,
            "Quality draft",
            confidence_score=0.82,
            confidence_label="High",
            moderation_passed=True,
            moderation_flags=[],
            generation_source="llm",
            llm_model="claude-sonnet-4-6",
            pipeline_latency_ms=latency,
        )
        draft.status = status
        test_db.commit()
        return draft

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

    def test_get_twin_quality_summary(self, client, auth_headers, test_db, test_user_data):
        """Quality summary should return 7-day dashboard metrics."""
        user = test_db.query(User).filter(User.email == test_user_data["email"]).first()
        self._seed_quality_draft(test_db, user, status="approved", latency=300)
        self._seed_quality_draft(test_db, user, status="edited", latency=500)
        self._seed_quality_draft(test_db, user, status="rejected", latency=700)

        response = client.get("/v1/twin/quality-summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["twin_id"] == user.twin.id
        assert data["drafts_handled_7d"] == 3
        assert data["approval_rate_7d"] == pytest.approx(0.6667, abs=0.001)
        assert data["avg_pipeline_latency_ms_7d"] == 500
        assert data["quality_label"] in {"excellent", "good", "needs_attention"}
        assert isinstance(data["recommendation"], str)

    def test_get_twin_quality_summary_unauthorized(self, client):
        response = client.get("/v1/twin/quality-summary")
        assert response.status_code == 403

    def test_get_twin_weekly_digest(self, client, auth_headers, test_db, test_user_data):
        user = test_db.query(User).filter(User.email == test_user_data["email"]).first()
        self._seed_quality_draft(test_db, user, status="approved", latency=300, channel="gmail")
        self._seed_quality_draft(test_db, user, status="edited", latency=450, channel="gmail")
        self._seed_quality_draft(test_db, user, status="rejected", latency=700, channel="instagram_dm")

        response = client.get("/v1/twin/weekly-digest", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["twin_id"] == user.twin.id
        assert data["messages_received_7d"] == 3
        assert data["drafts_generated_7d"] == 3
        assert data["drafts_handled_7d"] == 2
        assert data["approval_rate_7d"] == pytest.approx(0.6667, abs=0.001)
        assert data["top_channel"] == "gmail"
        assert isinstance(data["summary_line"], str)
        assert "handled" in data["summary_line"]

    def test_get_twin_weekly_digest_unauthorized(self, client):
        response = client.get("/v1/twin/weekly-digest")
        assert response.status_code == 403

    def test_get_twin_performance_summary(self, client, auth_headers, test_db, test_user_data):
        user = test_db.query(User).filter(User.email == test_user_data["email"]).first()
        self._seed_quality_draft(test_db, user, status="approved", latency=3500)
        self._seed_quality_draft(test_db, user, status="edited", latency=9200)
        self._seed_quality_draft(test_db, user, status="rejected", latency=12000)

        response = client.get("/v1/twin/performance-summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["twin_id"] == user.twin.id
        assert data["drafts_measured_7d"] == 3
        assert data["avg_pipeline_latency_ms_7d"] == 8233
        assert data["p95_pipeline_latency_ms_7d"] >= 9200
        assert data["drafts_over_10s_7d"] == 1
        assert data["on_target_under_10s"] is False
        assert isinstance(data["recommendation"], str)

    def test_get_twin_performance_summary_no_data(self, client, auth_headers):
        response = client.get("/v1/twin/performance-summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["drafts_measured_7d"] == 0
        assert data["on_target_under_10s"] is True

    def test_get_twin_performance_summary_unauthorized(self, client):
        response = client.get("/v1/twin/performance-summary")
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

    @patch("app.routers.drafts.get_settings")
    @patch("app.routers.drafts.synthesize_voice")
    def test_generate_voice_queues_task_for_approved_draft(
        self,
        mock_synthesize_voice,
        mock_settings,
        client,
        auth_headers,
        test_db,
        test_user_data,
    ):
        """Approved draft with consent should queue voice synthesis task."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)
        DraftService.approve_draft(test_db, draft.id, current_user.id)

        # Grant voice consent
        client.post("/v1/identity/voice/consent", headers=auth_headers, json={"granted": True})

        mock_settings.return_value.feature_voice_clone = True
        mock_task = MagicMock()
        mock_task.id = "task-voice-123"
        mock_synthesize_voice.delay.return_value = mock_task

        response = client.post(
            f"/v1/drafts/{draft.id}/voice/generate",
            headers=auth_headers,
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["draft_id"] == draft.id
        assert data["queued"] is True
        assert data["voice_status"] == "queued"
        assert data["task_id"] == "task-voice-123"

    @patch("app.routers.drafts.get_settings")
    def test_generate_voice_requires_consent(
        self,
        mock_settings,
        client,
        auth_headers,
        test_db,
        test_user_data,
    ):
        """Voice generation should fail when consent is missing."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)
        DraftService.approve_draft(test_db, draft.id, current_user.id)

        mock_settings.return_value.feature_voice_clone = True

        response = client.post(
            f"/v1/drafts/{draft.id}/voice/generate",
            headers=auth_headers,
            json={},
        )

        assert response.status_code == 409

    @patch("app.routers.drafts.get_settings")
    def test_generate_voice_requires_approved_or_edited_status(
        self,
        mock_settings,
        client,
        auth_headers,
        test_db,
        test_user_data,
    ):
        """Pending drafts cannot be queued for voice synthesis."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)

        client.post("/v1/identity/voice/consent", headers=auth_headers, json={"granted": True})
        mock_settings.return_value.feature_voice_clone = True

        response = client.post(
            f"/v1/drafts/{draft.id}/voice/generate",
            headers=auth_headers,
            json={},
        )

        assert response.status_code == 409

    @patch("app.routers.drafts.get_settings")
    def test_generate_voice_disabled_feature_returns_503(
        self,
        mock_settings,
        client,
        auth_headers,
        test_db,
        test_user_data,
    ):
        """Feature flag off should return service unavailable."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)
        DraftService.approve_draft(test_db, draft.id, current_user.id)

        client.post("/v1/identity/voice/consent", headers=auth_headers, json={"granted": True})
        mock_settings.return_value.feature_voice_clone = False

        response = client.post(
            f"/v1/drafts/{draft.id}/voice/generate",
            headers=auth_headers,
            json={},
        )

        assert response.status_code == 503

    def test_get_draft_voice_status(self, client, auth_headers, test_db, test_user_data):
        """Voice status endpoint should return persisted voice metadata."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)

        DraftService.set_voice_status(
            test_db,
            draft.id,
            voice_status="generated",
            voice_audio_url="mock://voice/test.mp3",
            voice_provider="mock",
            voice_model_id="voice-test-1",
            voice_error=None,
        )

        response = client.get(f"/v1/drafts/{draft.id}/voice", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["voice_status"] == "generated"
        assert data["voice_audio_url"] == "mock://voice/test.mp3"
        assert data["voice_provider"] == "mock"
        assert data["voice_model_id"] == "voice-test-1"

    @patch("app.routers.drafts.get_settings")
    @patch("app.routers.drafts.generate_avatar")
    def test_generate_avatar_queues_task_for_approved_draft(
        self,
        mock_generate_avatar,
        mock_settings,
        client,
        auth_headers,
        test_db,
        test_user_data,
    ):
        """Approved draft with consent should queue avatar generation task."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)
        DraftService.approve_draft(test_db, draft.id, current_user.id)

        # Grant avatar consent
        client.post("/v1/identity/avatar/consent", headers=auth_headers, json={"granted": True})

        mock_settings.return_value.feature_avatar_clone = True
        mock_task = MagicMock()
        mock_task.id = "task-avatar-123"
        mock_generate_avatar.delay.return_value = mock_task

        response = client.post(
            f"/v1/drafts/{draft.id}/avatar/generate",
            headers=auth_headers,
            json={"avatar_model_id": "avatar-test-1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["draft_id"] == draft.id
        assert data["queued"] is True
        assert data["avatar_status"] == "queued"
        assert data["task_id"] == "task-avatar-123"

    @patch("app.routers.drafts.get_settings")
    def test_generate_avatar_requires_consent(
        self,
        mock_settings,
        client,
        auth_headers,
        test_db,
        test_user_data,
    ):
        """Avatar generation should fail when consent is missing."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)
        DraftService.approve_draft(test_db, draft.id, current_user.id)

        mock_settings.return_value.feature_avatar_clone = True

        response = client.post(
            f"/v1/drafts/{draft.id}/avatar/generate",
            headers=auth_headers,
            json={},
        )

        assert response.status_code == 409

    @patch("app.routers.drafts.get_settings")
    def test_generate_avatar_requires_approved_or_edited_status(
        self,
        mock_settings,
        client,
        auth_headers,
        test_db,
        test_user_data,
    ):
        """Pending drafts cannot be queued for avatar generation."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)

        client.post("/v1/identity/avatar/consent", headers=auth_headers, json={"granted": True})
        mock_settings.return_value.feature_avatar_clone = True

        response = client.post(
            f"/v1/drafts/{draft.id}/avatar/generate",
            headers=auth_headers,
            json={},
        )

        assert response.status_code == 409

    @patch("app.routers.drafts.get_settings")
    def test_generate_avatar_disabled_feature_returns_503(
        self,
        mock_settings,
        client,
        auth_headers,
        test_db,
        test_user_data,
    ):
        """Feature flag off should return service unavailable."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)
        DraftService.approve_draft(test_db, draft.id, current_user.id)

        client.post("/v1/identity/avatar/consent", headers=auth_headers, json={"granted": True})
        mock_settings.return_value.feature_avatar_clone = False

        response = client.post(
            f"/v1/drafts/{draft.id}/avatar/generate",
            headers=auth_headers,
            json={},
        )

        assert response.status_code == 503

    def test_get_draft_avatar_status(self, client, auth_headers, test_db, test_user_data):
        """Avatar status endpoint should return persisted avatar metadata."""
        current_user = self._get_authenticated_user(test_db, test_user_data)
        draft = self._seed_draft(test_db, current_user)

        DraftService.set_avatar_status(
            test_db,
            draft.id,
            avatar_status="generated",
            avatar_video_url="mock://avatar/test.mp4",
            avatar_provider="mock",
            avatar_model_id="avatar-test-1",
            avatar_error=None,
        )

        response = client.get(f"/v1/drafts/{draft.id}/avatar", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["avatar_status"] == "generated"
        assert data["avatar_video_url"] == "mock://avatar/test.mp4"
        assert data["avatar_provider"] == "mock"
        assert data["avatar_model_id"] == "avatar-test-1"


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


class TestChannelEndpoints:
    """Tests for channel credential management endpoints."""

    def test_connect_and_list_channels(self, client, auth_headers):
        connect_instagram = client.post(
            "/v1/channels/instagram/connect",
            headers=auth_headers,
            json={},
        )
        connect_gmail = client.post(
            "/v1/channels/gmail/connect",
            headers=auth_headers,
            json={},
        )

        assert connect_instagram.status_code == 200
        assert connect_gmail.status_code == 200

        response = client.get("/v1/channels/connected", headers=auth_headers)
        assert response.status_code == 200

        channels = {item["channel"]: item for item in response.json()}
        assert channels["instagram_dm"]["connected"] is True
        assert channels["gmail"]["connected"] is True

    def test_disconnect_channel(self, client, auth_headers):
        client.post(
            "/v1/channels/instagram/connect",
            headers=auth_headers,
            json={},
        )

        response = client.post(
            "/v1/channels/instagram/disconnect",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["connected"] is False

    def test_connect_requires_auth(self, client):
        response = client.post("/v1/channels/gmail/connect", json={})
        assert response.status_code == 403


class TestReferralEndpoints:
    """Tests for creator referral flow endpoints."""

    @staticmethod
    def _login_headers(client, email: str, password: str):
        response = client.post(
            "/v1/auth/login",
            json={"email": email, "password": password},
        )
        token = response.json()["tokens"]["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_invite_and_summary(self, client, auth_headers):
        invite_response = client.post(
            "/v1/referrals/invite",
            headers=auth_headers,
            json={"invitee_email": "creator2@example.com"},
        )
        assert invite_response.status_code == 201
        invite_data = invite_response.json()
        assert invite_data["status"] == "pending"
        assert invite_data["referral_code"]

        summary_response = client.get("/v1/referrals/summary", headers=auth_headers)
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["total_invites"] == 1
        assert summary["pending_invites"] == 1
        assert summary["accepted_invites"] == 0
        assert summary["reward_months_earned"] == 0

    def test_accept_referral_updates_reward_months(self, client, auth_headers):
        invite_response = client.post(
            "/v1/referrals/invite",
            headers=auth_headers,
            json={"invitee_email": "creator3@example.com"},
        )
        code = invite_response.json()["referral_code"]

        second_user = {
            "email": "creator3@example.com",
            "password": "TestPassword123",
            "name": "Creator Three",
        }
        signup = client.post("/v1/auth/signup", json=second_user)
        assert signup.status_code == 201
        second_headers = self._login_headers(client, second_user["email"], second_user["password"])

        accept_response = client.post(
            "/v1/referrals/accept",
            headers=second_headers,
            json={"referral_code": code},
        )
        assert accept_response.status_code == 200
        assert accept_response.json()["status"] == "accepted"

        referrer_summary = client.get("/v1/referrals/summary", headers=auth_headers).json()
        assert referrer_summary["accepted_invites"] == 1
        assert referrer_summary["reward_months_earned"] == 1

    def test_cannot_invite_self_email(self, client, auth_headers, test_user_data):
        response = client.post(
            "/v1/referrals/invite",
            headers=auth_headers,
            json={"invitee_email": test_user_data["email"]},
        )
        assert response.status_code == 400

    def test_referral_summary_requires_auth(self, client):
        response = client.get("/v1/referrals/summary")
        assert response.status_code == 403

    def test_referral_code_cannot_be_claimed_by_second_user(self, client, auth_headers):
        invite_response = client.post(
            "/v1/referrals/invite",
            headers=auth_headers,
            json={"invitee_email": "creator4@example.com"},
        )
        code = invite_response.json()["referral_code"]

        first_invitee = {
            "email": "creator4@example.com",
            "password": "TestPassword123",
            "name": "Creator Four",
        }
        second_invitee = {
            "email": "creator5@example.com",
            "password": "TestPassword123",
            "name": "Creator Five",
        }
        assert client.post("/v1/auth/signup", json=first_invitee).status_code == 201
        assert client.post("/v1/auth/signup", json=second_invitee).status_code == 201

        first_headers = self._login_headers(client, first_invitee["email"], first_invitee["password"])
        second_headers = self._login_headers(client, second_invitee["email"], second_invitee["password"])

        first_accept = client.post(
            "/v1/referrals/accept",
            headers=first_headers,
            json={"referral_code": code},
        )
        assert first_accept.status_code == 200

        second_accept = client.post(
            "/v1/referrals/accept",
            headers=second_headers,
            json={"referral_code": code},
        )
        assert second_accept.status_code == 409

    def test_referrer_cannot_accept_own_referral_code(self, client, auth_headers):
        invite_response = client.post(
            "/v1/referrals/invite",
            headers=auth_headers,
            json={"invitee_email": "creator6@example.com"},
        )
        code = invite_response.json()["referral_code"]

        accept_response = client.post(
            "/v1/referrals/accept",
            headers=auth_headers,
            json={"referral_code": code},
        )
        assert accept_response.status_code == 409


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "ok"]

    def test_readiness_check_healthy(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"]["ok"] is True
        assert data["checks"]["jwt_secret"]["ok"] is True

    @patch("app.routers.health.get_settings")
    def test_readiness_check_detects_insecure_production_jwt(self, mock_get_settings, client):
        mock_get_settings.return_value = SimpleNamespace(
            environment="production",
            enforce_production_jwt_secret=True,
            jwt_secret_key="dev-secret-key-change-in-production",
        )

        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["jwt_secret"]["ok"] is False
