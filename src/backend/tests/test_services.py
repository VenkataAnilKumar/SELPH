"""
Unit tests for backend services
"""

import pytest
from app.services.auth import AuthService
from app.services.twin import TwinService
from app.services.identity import IdentityService
from app.services.message import MessageService
from app.services.draft import DraftService
from app.services.moderation import ModerationService
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
