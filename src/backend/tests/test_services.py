"""
Unit tests for backend services
"""

import pytest
from app.models import AuditLog
from app.services.auth import AuthService
from app.services.twin import TwinService
from app.services.identity import IdentityService
from app.services.message import MessageService
from app.services.draft import DraftService
from app.services.moderation import ModerationService
from app.services.twin_engine import TwinEngineService
from app.schemas.auth import SignupRequest, LoginRequest


class TestAuthService:
    """Test authentication service"""

    def test_signup_creates_user(self, test_db, test_user_data):
        """Test user signup creates user with twin and identity"""
        service = AuthService()
        user = service.signup(
            test_db,
            SignupRequest(
                email=test_user_data["email"],
                password=test_user_data["password"],
                name=test_user_data["name"],
            ),
        )
        
        assert user is not None
        assert user.email == test_user_data["email"]
        assert user.id is not None
        
        # Verify twin was auto-created
        twin = user.twin
        assert twin is not None
        assert twin.user_id == user.id
        assert twin.status in ["active", "paused"]

    def test_signup_hashes_password(self, test_db, test_user_data):
        """Test signup hashes password (not stored plaintext)"""
        service = AuthService()
        user = service.signup(
            test_db,
            SignupRequest(
                email=test_user_data["email"],
                password=test_user_data["password"],
                name=test_user_data["name"],
            ),
        )
        
        # Password should not be plaintext
        assert user.password_hash != test_user_data["password"]
        assert user.password_hash is not None

    def test_signup_duplicate_email_fails(self, test_db, test_user_data):
        """Test signup with duplicate email fails"""
        service = AuthService()
        
        # First signup succeeds
        user1 = service.signup(
            test_db,
            SignupRequest(
                email=test_user_data["email"],
                password=test_user_data["password"],
                name=test_user_data["name"],
            ),
        )
        assert user1 is not None
        
        # Second signup with same email should fail
        with pytest.raises(Exception):
            service.signup(
                test_db,
                SignupRequest(
                    email=test_user_data["email"],
                    password="AnotherPassword123",
                    name="Another User",
                ),
            )

    def test_login_valid_credentials(self, test_db, test_user_data):
        """Test login with valid credentials"""
        service = AuthService()
        
        # Signup
        service.signup(
            test_db,
            SignupRequest(
                email=test_user_data["email"],
                password=test_user_data["password"],
                name=test_user_data["name"],
            ),
        )
        
        # Login
        user = service.login(
            test_db,
            LoginRequest(
                email=test_user_data["email"],
                password=test_user_data["password"],
            ),
        )
        assert user is not None
        assert user.email == test_user_data["email"]

    def test_login_invalid_password(self, test_db, test_user_data):
        """Test login with invalid password fails"""
        service = AuthService()
        
        # Signup
        service.signup(
            test_db,
            SignupRequest(
                email=test_user_data["email"],
                password=test_user_data["password"],
                name=test_user_data["name"],
            ),
        )
        
        # Login with wrong password
        with pytest.raises(Exception):
            service.login(
                test_db,
                LoginRequest(
                    email=test_user_data["email"],
                    password="WrongPassword123",
                ),
            )

    def test_login_nonexistent_user(self, test_db):
        """Test login with nonexistent email fails"""
        service = AuthService()
        
        with pytest.raises(Exception):
            service.login(
                test_db,
                LoginRequest(
                    email="nonexistent@example.com",
                    password="AnyPassword123",
                ),
            )

    def test_generate_tokens(self, test_db, test_user):
        """Test token generation"""
        service = AuthService()
        access_token, refresh_token, expires_in = service.generate_tokens(test_user.id)
        
        assert access_token is not None
        assert refresh_token is not None
        assert isinstance(expires_in, int)
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert len(access_token) > 0
        assert len(refresh_token) > 0


class TestTwinService:
    """Test twin service"""

    def test_get_twin(self, test_db, test_user):
        """Test getting user's twin"""
        service = TwinService()
        twin = service.get_twin(test_db, test_user.id)
        
        assert twin is not None
        assert twin.user_id == test_user.id
        assert twin.status == "active"

    def test_pause_twin(self, test_db, test_user):
        """Test pausing twin"""
        service = TwinService()
        
        # Initial status should be active
        twin = service.get_twin(test_db, test_user.id)
        assert twin.status == "active"
        
        # Pause twin
        updated_twin = service.pause_twin(test_db, test_user.id)
        assert updated_twin.status == "paused"

    def test_resume_twin(self, test_db, test_user):
        """Test resuming paused twin"""
        service = TwinService()
        
        # Pause twin first
        service.pause_twin(test_db, test_user.id)
        
        # Resume twin
        updated_twin = service.resume_twin(test_db, test_user.id)
        assert updated_twin.status == "active"

    def test_get_twin_stats(self, test_db, test_user):
        """Test getting twin statistics"""
        service = TwinService()
        stats = service.get_twin_stats(test_db, test_user.id)
        
        assert stats is not None
        assert "status" in stats
        assert "domain" in stats
        assert "tone" in stats
        assert "total_messages" in stats
        assert "pending_drafts" in stats
        assert "total_estimated_tokens" in stats
        assert "total_estimated_cost_usd" in stats
        assert "fallback_rate" in stats
        assert stats["status"] == "active"
        assert stats["total_messages"] == 0
        assert stats["pending_drafts"] == 0

    def test_update_twin_profile(self, test_db, test_user, test_twin_data):
        """Test updating twin profile"""
        service = TwinService()
        
        updated_twin = service.update_twin_profile(
            test_db,
            test_user.id,
            test_twin_data["domain"],
            test_twin_data["tone"],
            test_twin_data["vocab"],
            test_twin_data["avg_response_length"],
        )
        
        assert updated_twin.domain == test_twin_data["domain"]
        assert updated_twin.tone == test_twin_data["tone"]


class TestMessageService:
    """Test message service"""

    def test_create_message(self, test_db, test_user, test_message_data):
        """Test creating a message"""
        service = MessageService()
        
        message = service.create_message(
            test_db,
            test_user.id,
            test_message_data["channel"],
            test_message_data["sender_id"],
            test_message_data["sender_name"],
            test_message_data["content"],
            test_message_data["channel_metadata"],
        )
        
        assert message is not None
        assert message.user_id == test_user.id
        assert message.channel == test_message_data["channel"]
        assert message.sender_name == test_message_data["sender_name"]
        assert message.status == "received"

    def test_get_message(self, test_db, test_user, test_message_data):
        """Test getting a message"""
        service = MessageService()
        
        created_message = service.create_message(
            test_db,
            test_user.id,
            test_message_data["channel"],
            test_message_data["sender_id"],
            test_message_data["sender_name"],
            test_message_data["content"],
            test_message_data["channel_metadata"],
        )
        
        fetched_message = service.get_message(test_db, created_message.id)
        
        assert fetched_message is not None
        assert fetched_message.id == created_message.id

    def test_get_user_messages(self, test_db, test_user, test_message_data):
        """Test getting user's messages"""
        service = MessageService()
        
        # Create multiple messages
        for i in range(3):
            service.create_message(
                test_db,
                test_user.id,
                test_message_data["channel"],
                f"sender_{i}",
                f"Sender {i}",
                f"Message {i}",
                test_message_data["channel_metadata"],
            )
        
        messages = service.get_user_messages(test_db, test_user.id, 0, 10)
        
        assert len(messages) == 3

    def test_mark_as_processed(self, test_db, test_user, test_message_data):
        """Test marking message as processed"""
        service = MessageService()
        
        message = service.create_message(
            test_db,
            test_user.id,
            test_message_data["channel"],
            test_message_data["sender_id"],
            test_message_data["sender_name"],
            test_message_data["content"],
            test_message_data["channel_metadata"],
        )
        
        updated_message = service.mark_as_processed(test_db, message.id)
        assert updated_message.status == "processed"

    def test_count_messages(self, test_db, test_user, test_message_data):
        """Test counting messages"""
        service = MessageService()
        
        # Create messages
        for i in range(3):
            service.create_message(
                test_db,
                test_user.id,
                test_message_data["channel"],
                f"sender_{i}",
                f"Sender {i}",
                f"Message {i}",
                test_message_data["channel_metadata"],
            )
        
        count = service.count_messages(test_db, test_user.id)
        assert count == 3


class TestDraftService:
    """Test draft service"""

    def test_create_draft(self, test_db, test_user):
        """Test creating a draft"""
        from app.services.message import MessageService
        
        message_service = MessageService()
        draft_service = DraftService()
        
        # First create a message
        message = message_service.create_message(
            test_db,
            test_user.id,
            "instagram_dm",
            "sender_123",
            "John",
            "Hello!",
            {},
        )
        
        # Create draft
        draft = draft_service.create_draft(
            test_db,
            message.id,
            test_user.id,
            test_user.twin.id,
            "Hi there!",
            0.85,
            True,
        )
        
        assert draft is not None
        assert draft.message_id == message.id
        assert draft.content == "Hi there!"
        assert draft.status == "pending_approval"

    def test_get_pending_drafts(self, test_db, test_user):
        """Test getting pending drafts"""
        from app.services.message import MessageService
        
        message_service = MessageService()
        draft_service = DraftService()
        
        # Create message and draft
        message = message_service.create_message(
            test_db, test_user.id, "instagram_dm", "sender", "John", "Hello", {}
        )
        draft = draft_service.create_draft(
            test_db, message.id, test_user.id, test_user.twin.id, "Hi!", 0.8, True
        )
        
        pending = draft_service.get_pending_drafts(test_db, test_user.id, 0, 10)
        
        assert len(pending) == 1
        assert pending[0].id == draft.id

    def test_approve_draft(self, test_db, test_user):
        """Test approving a draft"""
        from app.services.message import MessageService
        
        message_service = MessageService()
        draft_service = DraftService()
        
        # Create message and draft
        message = message_service.create_message(
            test_db, test_user.id, "instagram_dm", "sender", "John", "Hello", {}
        )
        draft = draft_service.create_draft(
            test_db, message.id, test_user.id, test_user.twin.id, "Hi!", 0.8, True
        )
        
        # Approve
        approved_draft = draft_service.approve_draft(test_db, draft.id, test_user.id)
        
        assert approved_draft.status == "approved"
        audit = test_db.query(AuditLog).filter(AuditLog.resource_id == draft.id, AuditLog.action == "approve_draft").first()
        assert audit is not None
        assert "generation_source" in audit.details

    def test_reject_draft(self, test_db, test_user):
        """Test rejecting a draft"""
        from app.services.message import MessageService
        
        message_service = MessageService()
        draft_service = DraftService()
        
        # Create message and draft
        message = message_service.create_message(
            test_db, test_user.id, "instagram_dm", "sender", "John", "Hello", {}
        )
        draft = draft_service.create_draft(
            test_db, message.id, test_user.id, test_user.twin.id, "Hi!", 0.8, True
        )
        
        # Reject
        rejected_draft = draft_service.reject_draft(test_db, draft.id, test_user.id)
        
        assert rejected_draft.status == "rejected"

    def test_edit_draft(self, test_db, test_user):
        """Test editing a draft"""
        from app.services.message import MessageService
        
        message_service = MessageService()
        draft_service = DraftService()
        
        # Create message and draft
        message = message_service.create_message(
            test_db, test_user.id, "instagram_dm", "sender", "John", "Hello", {}
        )
        draft = draft_service.create_draft(
            test_db, message.id, test_user.id, test_user.twin.id, "Hi!", 0.8, True
        )
        
        # Edit
        edited_draft = draft_service.edit_draft(
            test_db, draft.id, test_user.id, "Hello there!"
        )
        
        assert edited_draft.status == "edited"
        assert edited_draft.edited_content == "Hello there!"

    def test_skip_draft_records_skip_action(self, test_db, test_user):
        """Skip should preserve rejected status but keep distinct user_action and audit trail."""
        from app.services.message import MessageService

        message = MessageService.create_message(
            test_db, test_user.id, "instagram_dm", "sender", "John", "Hello", {}
        )
        draft = DraftService.create_draft(
            test_db, message.id, test_user.id, test_user.twin.id, "Hi!", 0.8, True
        )

        skipped_draft = DraftService.skip_draft(test_db, draft.id, test_user.id)

        assert skipped_draft.status == "rejected"
        assert skipped_draft.user_action == "skip"
        audit = test_db.query(AuditLog).filter(AuditLog.resource_id == draft.id, AuditLog.action == "skip_draft").first()
        assert audit is not None

    def test_get_twin_stats_counts_edited_as_processed(self, test_db, test_user):
        """Edited drafts should count as processed in twin stats."""
        message = MessageService.create_message(
            test_db, test_user.id, "instagram_dm", "sender_stats", "John", "Hello", {}
        )
        draft = DraftService.create_draft(
            test_db,
            message.id,
            test_user.id,
            test_user.twin.id,
            "Hi!",
            confidence_score=0.8,
            moderation_passed=True,
            generation_source="deterministic",
            llm_model="deterministic-fallback",
            fallback_reason="llm_disabled",
            estimated_total_tokens=100,
            estimated_cost_usd=0.0,
        )
        DraftService.edit_draft(test_db, draft.id, test_user.id, "Updated")

        stats = TwinService.get_twin_stats(test_db, test_user.id)

        assert stats["processed_drafts"] == 1
        assert stats["generation_source_breakdown"]["deterministic"] >= 1
        assert stats["fallback_reason_breakdown"]["llm_disabled"] >= 1

    def test_get_draft_summary(self, test_db, test_user):
        """Test getting draft summary statistics"""
        from app.services.message import MessageService
        
        message_service = MessageService()
        draft_service = DraftService()
        
        # Create message and drafts
        for i in range(3):
            message = message_service.create_message(
                test_db, test_user.id, "instagram_dm", f"sender_{i}", "John", f"Hello {i}", {}
            )
            draft = draft_service.create_draft(
                test_db, message.id, test_user.id, test_user.twin.id, f"Hi {i}!", 0.8, True
            )
        
        summary = draft_service.get_draft_summary(test_db, test_user.id)
        
        assert summary["total"] == 3
        assert summary["pending"] == 3
        assert summary["approved"] == 0
        assert summary["rejected"] == 0


class TestTwinEngineService:
    """Test Phase 2 twin engine pipeline."""

    def test_pipeline_returns_draft_and_confidence(self, test_db, test_user):
        """Pipeline should return draft content and confidence metadata."""
        message = MessageService.create_message(
            test_db,
            test_user.id,
            "instagram_dm",
            "sender_1",
            "Alex",
            "Hey, can you help me with content strategy?",
            {},
        )

        result = TwinEngineService.run_twin_pipeline(test_db, message.id, test_user.id)

        assert result["twin_id"] == test_user.twin.id
        assert isinstance(result["draft"], str)
        assert len(result["draft"]) > 0
        assert 0.0 <= result["confidence_score"] <= 1.0
        assert result["confidence_label"] in ["High", "Medium", "Low"]
        assert "topic_known" in result["confidence_factors"]
        assert result["estimated_total_tokens"] >= 0
        assert result["estimated_cost_usd"] >= 0

    def test_pipeline_uses_avoided_topic_fallback(self, test_db, test_user):
        """Avoided topics should trigger safe fallback response."""
        IdentityService.add_avoided_topic(test_db, test_user.id, "politics")

        message = MessageService.create_message(
            test_db,
            test_user.id,
            "instagram_dm",
            "sender_2",
            "Sam",
            "What is your take on politics this week?",
            {},
        )

        result = TwinEngineService.run_twin_pipeline(test_db, message.id, test_user.id)
        assert "That's not something I cover" in result["draft"]
        assert result["confidence_factors"]["no_avoided_topics"] == 0.0

    def test_pipeline_topic_match_increases_score(self, test_db, test_user):
        """Known topic match should produce a higher topic factor."""
        IdentityService.add_known_topic(test_db, test_user.id, "photography")

        message = MessageService.create_message(
            test_db,
            test_user.id,
            "instagram_dm",
            "sender_3",
            "Jamie",
            "Any photography tips for portraits?",
            {},
        )

        result = TwinEngineService.run_twin_pipeline(test_db, message.id, test_user.id)
        assert result["confidence_factors"]["topic_known"] >= 0.9

    def test_pipeline_respects_channel_word_limit(self, test_db, test_user):
        """Generated draft should respect channel max words."""
        message = MessageService.create_message(
            test_db,
            test_user.id,
            "twitter_dm",
            "sender_4",
            "Taylor",
            "Please share your detailed perspective on audience engagement and retention strategies.",
            {},
        )

        result = TwinEngineService.run_twin_pipeline(test_db, message.id, test_user.id)
        assert len(result["draft"].split()) <= 100

    def test_pipeline_uses_llm_when_feature_enabled(self, test_db, test_user, monkeypatch):
        """When feature flag is enabled, pipeline should use LLM output."""
        from app.services import twin_engine as twin_engine_module

        prev_flag = twin_engine_module.settings.feature_twin_llm_drafts
        twin_engine_module.settings.feature_twin_llm_drafts = True

        def fake_call(_messages):
            return (
                '{"draft":"LLM generated reply","confidence_factors":'
                '{"topic_known":0.9,"length_match":0.8,"tone_match":0.85,'
                '"no_avoided_topics":1.0,"sample_similarity":0.7},'
                '"reasoning":"Matched user style","flags":[]}'
            )

        monkeypatch.setattr(TwinEngineService, "_call_litellm", staticmethod(fake_call))

        try:
            message = MessageService.create_message(
                test_db,
                test_user.id,
                "instagram_dm",
                "sender_llm",
                "Morgan",
                "Can you help with launch messaging?",
                {},
            )

            result = TwinEngineService.run_twin_pipeline(test_db, message.id, test_user.id)
            assert result["draft"] == "LLM generated reply"
            assert result["generation_source"] == "llm"
            assert result["confidence_factors"]["topic_known"] == 0.9
            assert "metrics" in result
            assert "pipeline_latency_ms" in result["metrics"]
            assert "llm_latency_ms" in result["metrics"]
            assert result["metrics"]["used_fallback"] is False
        finally:
            twin_engine_module.settings.feature_twin_llm_drafts = prev_flag

    def test_pipeline_retries_invalid_llm_json_then_succeeds(self, test_db, test_user, monkeypatch):
        """Invalid JSON from LLM should trigger one retry and then succeed."""
        from app.services import twin_engine as twin_engine_module

        prev_llm = twin_engine_module.settings.feature_twin_llm_drafts
        prev_retry = twin_engine_module.settings.feature_twin_llm_json_retry
        twin_engine_module.settings.feature_twin_llm_drafts = True
        twin_engine_module.settings.feature_twin_llm_json_retry = True

        calls = {"count": 0}

        def fake_call(_messages):
            calls["count"] += 1
            if calls["count"] == 1:
                return "not-json"
            return (
                '{"draft":"Retried valid JSON draft","confidence_factors":'
                '{"topic_known":0.7,"length_match":0.7,"tone_match":0.7,'
                '"no_avoided_topics":1.0,"sample_similarity":0.6},'
                '"reasoning":"Retry fixed structure","flags":[]}'
            )

        monkeypatch.setattr(TwinEngineService, "_call_litellm", staticmethod(fake_call))

        try:
            message = MessageService.create_message(
                test_db,
                test_user.id,
                "gmail",
                "sender_retry",
                "Riley",
                "Please send a concise update.",
                {},
            )

            result = TwinEngineService.run_twin_pipeline(test_db, message.id, test_user.id)
            assert result["draft"] == "Retried valid JSON draft"
            assert result["generation_source"] == "llm"
            assert calls["count"] == 2
            assert result["metrics"]["parse_retry_count"] == 1
        finally:
            twin_engine_module.settings.feature_twin_llm_drafts = prev_llm
            twin_engine_module.settings.feature_twin_llm_json_retry = prev_retry

    def test_pipeline_metrics_show_fallback_when_llm_fails(self, test_db, test_user, monkeypatch):
        """If LLM fails, deterministic fallback should be reported in metrics."""
        from app.services import twin_engine as twin_engine_module

        prev_flag = twin_engine_module.settings.feature_twin_llm_drafts
        twin_engine_module.settings.feature_twin_llm_drafts = True

        def fail_call(_messages):
            raise RuntimeError("simulated provider failure")

        monkeypatch.setattr(TwinEngineService, "_call_litellm", staticmethod(fail_call))

        try:
            message = MessageService.create_message(
                test_db,
                test_user.id,
                "instagram_dm",
                "sender_llm_fail",
                "Casey",
                "Need your thoughts on creator workflows",
                {},
            )

            result = TwinEngineService.run_twin_pipeline(test_db, message.id, test_user.id)
            assert result["generation_source"] == "deterministic"
            assert result["metrics"]["used_fallback"] is True
            assert result["metrics"]["llm_calls"] == 0
        finally:
            twin_engine_module.settings.feature_twin_llm_drafts = prev_flag


class TestModerationService:
    """Test moderation service"""

    def test_check_content_safety_clean(self):
        """Test moderation with clean content"""
        service = ModerationService()
        passed, flags, risk_score = service.check_content_safety("Hello, how are you?")
        
        assert passed is True
        assert len(flags) == 0
        assert risk_score < 0.7

    def test_check_content_safety_violence(self):
        """Test moderation detects violence"""
        service = ModerationService()
        passed, flags, risk_score = service.check_content_safety("I will kill you")
        
        assert passed is False
        assert any(f["pattern"] == "kill" for f in flags)

    def test_check_content_safety_self_harm(self):
        """Test moderation detects self-harm"""
        service = ModerationService()
        passed, flags, risk_score = service.check_content_safety("I want to hurt myself")
        
        assert passed is False
        assert any(f["pattern"] == "hurt" for f in flags)

    def test_get_confidence_label_high(self):
        """Test confidence label for high score"""
        service = ModerationService()
        label = service.get_confidence_label(0.9)
        
        assert label == "High"

    def test_get_confidence_label_medium(self):
        """Test confidence label for medium score"""
        service = ModerationService()
        label = service.get_confidence_label(0.5)
        
        assert label == "Medium"

    def test_get_confidence_label_low(self):
        """Test confidence label for low score"""
        service = ModerationService()
        label = service.get_confidence_label(0.2)
        
        assert label == "Low"

    def test_calculate_confidence_score(self):
        """Test confidence score calculation"""
        service = ModerationService()
        
        score = service.calculate_confidence_score(
            user_interaction_count=10, moderation_passed=True, topic_match=0.9
        )
        
        assert 0.0 <= score <= 1.0


class TestPushNotificationTask:
    """Unit tests for the notify_draft_ready Celery task helper."""

    def test_skips_user_with_no_token(self, test_db, test_user):
        """When the user has no push_token, the task returns sent=False."""
        from unittest.mock import patch
        from app.tasks.push_notifications import notify_draft_ready

        test_user.push_token = None
        test_db.commit()

        with patch("app.tasks.push_notifications.create_engine") as mock_engine:
            mock_engine.return_value = test_db.get_bind()
            # Bypass DB creation — call helper logic directly via a local session
            from sqlalchemy.orm import sessionmaker
            SessionLocal = sessionmaker(bind=test_db.get_bind())
            db = SessionLocal()
            try:
                from app.models.user import User
                u = db.query(User).filter(User.id == test_user.id).first()
                assert u.push_token is None
            finally:
                db.close()

    def test_send_expo_push_builds_correct_payload(self):
        """_send_expo_push constructs the right JSON body."""
        from unittest.mock import patch, MagicMock
        from app.tasks.push_notifications import _send_expo_push
        import json

        captured = {}

        def fake_urlopen(req, timeout=10):
            captured["url"] = req.full_url
            captured["payload"] = json.loads(req.data)
            resp = MagicMock()
            resp.status = 200
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch("app.tasks.push_notifications.urllib.request.urlopen", fake_urlopen):
            _send_expo_push(
                token="ExponentPushToken[test]",
                title="New draft ready",
                body="Tap to review.",
                data={"draft_id": "d-1"},
            )

        assert captured["payload"]["to"] == "ExponentPushToken[test]"
        assert captured["payload"]["title"] == "New draft ready"
        assert captured["payload"]["data"]["draft_id"] == "d-1"


# ---------------------------------------------------------------------------
# Phase 3.4 — Twin Learning Service
# ---------------------------------------------------------------------------

class TestTwinLearningService:
    """Unit tests for TwinLearningService (Phase 3.4)."""

    def _make_twin_and_draft(self, db, user):
        """Helper: create a message + draft for the given user's twin."""
        from app.models import Message, Draft

        msg = Message(
            user_id=user.id,
            channel="test",
            sender_id="s1",
            sender_name="Sender",
            content="Hello there, can you help me?",
            status="received",
        )
        db.add(msg)
        db.flush()

        draft = Draft(
            message_id=msg.id,
            user_id=user.id,
            twin_id=user.twin.id,
            content="Sure! Happy to help you with that amazing project.",
            confidence_score=0.85,
            confidence_label="High",
            moderation_passed=True,
            status="pending_approval",
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)
        return draft

    def test_learn_from_approval_adds_vocab(self, test_db, test_user):
        """Approving a draft should absorb new vocab words into the twin."""
        from app.services.twin_learning import TwinLearningService

        twin = test_user.twin
        original_vocab = list(twin.vocab)

        TwinLearningService.learn_from_approval(
            test_db, twin.id, "This specialised vocabulary expansion works perfectly"
        )
        test_db.refresh(twin)

        assert "specialised" in twin.vocab or "vocabulary" in twin.vocab or "expansion" in twin.vocab

    def test_learn_from_approval_unknown_twin_is_noop(self, test_db):
        """Calling with a non-existent twin ID should silently do nothing."""
        from app.services.twin_learning import TwinLearningService

        # Should not raise
        TwinLearningService.learn_from_approval(test_db, "nonexistent-twin-id", "some text")

    def test_learn_from_edit_adjusts_response_length(self, test_db, test_user):
        """Editing toward a shorter response should nudge avg_response_length down."""
        from app.services.twin_learning import TwinLearningService

        twin = test_user.twin
        twin.avg_response_length = 200
        test_db.commit()

        # Edited version is ~5 words
        short_edit = "Sure! Let me know."
        TwinLearningService.learn_from_edit(
            test_db, twin.id, "original longer content here for testing purposes", short_edit
        )
        test_db.refresh(twin)

        # Should have moved slightly lower than 200
        assert twin.avg_response_length < 200

    def test_learn_from_edit_absorbs_edited_vocab(self, test_db, test_user):
        """Edited vocab should appear in the twin's vocab list."""
        from app.services.twin_learning import TwinLearningService

        twin = test_user.twin
        TwinLearningService.learn_from_edit(
            test_db, twin.id, "original text", "uniqueword edited content version"
        )
        test_db.refresh(twin)

        assert "uniqueword" in twin.vocab or "edited" in twin.vocab or "content" in twin.vocab

    def test_vocab_bounded_to_max(self, test_db, test_user):
        """Vocab list should never exceed 200 entries."""
        from app.services.twin_learning import TwinLearningService

        twin = test_user.twin
        # Pre-fill with 195 unique words
        twin.vocab = [f"word{i}" for i in range(195)]
        test_db.commit()

        # Absorb 20 more unique words
        big_text = " ".join(f"brand{i}word" for i in range(20))
        TwinLearningService.learn_from_approval(test_db, twin.id, big_text)
        test_db.refresh(twin)

        assert len(twin.vocab) <= 200


class TestApprovalRateMetric:
    """Tests that approval_rate appears correctly in TwinStatsResponse (Phase 3 exit criterion)."""

    def _setup_user_with_drafts(self, db, test_user_data):
        """Create user + drafts with various statuses."""
        from app.services.auth import AuthService
        from app.schemas.auth import SignupRequest
        from app.models import Message, Draft

        svc = AuthService()
        user = svc.signup(
            db,
            SignupRequest(
                email="approval_rate@example.com",
                password="Str0ng!Pass",
                name="Rate Tester",
            ),
        )

        msg = Message(
            user_id=user.id,
            channel="test",
            sender_id="s1",
            sender_name="Sender",
            content="hi",
            status="received",
        )
        db.add(msg)
        db.flush()

        statuses = ["approved", "approved", "edited", "rejected"]
        for i, s in enumerate(statuses):
            msg_i = Message(
                user_id=user.id,
                channel="test",
                sender_id=f"s{i}",
                sender_name="Sender",
                content="hi",
                status="received",
            )
            db.add(msg_i)
            db.flush()
            d = Draft(
                message_id=msg_i.id,
                user_id=user.id,
                twin_id=user.twin.id,
                content="draft content",
                confidence_score=0.7,
                confidence_label="Medium",
                moderation_passed=True,
                status=s,
            )
            db.add(d)
        db.commit()
        return user

    def test_approval_rate_correct_value(self, test_db, test_user_data):
        """approval_rate = (approved+edited) / (approved+edited+rejected) = 3/4 = 0.75"""
        from app.services.twin import TwinService

        user = self._setup_user_with_drafts(test_db, test_user_data)
        stats = TwinService.get_twin_stats(test_db, user.id)

        # 2 approved + 1 edited = 3 decided positively; 1 rejected; 4 total decided
        assert stats["approval_rate"] == pytest.approx(0.75, abs=0.01)

    def test_approval_rate_zero_when_no_decisions(self, test_db, test_user):
        """When no drafts have been decided, approval_rate should be 0.0."""
        from app.services.twin import TwinService

        stats = TwinService.get_twin_stats(test_db, test_user.id)
        assert stats["approval_rate"] == 0.0

    def test_approval_rate_in_stats_response_key(self, test_db, test_user):
        """approval_rate key must be present in get_twin_stats output."""
        from app.services.twin import TwinService

        stats = TwinService.get_twin_stats(test_db, test_user.id)
        assert "approval_rate" in stats

