"""Phase 7 PR A tests: avatar provider abstraction and task foundation."""

from sqlalchemy.orm import sessionmaker

from app.avatar.registry import get_avatar_provider
from app.models import Draft, IdentityProfile, Message, Twin
from app.services import DraftService, MessageService
from app.tasks import avatar_generation


def _bind_task_engine_to_test_db(monkeypatch, test_db):
    engine = test_db.get_bind()
    monkeypatch.setattr(avatar_generation, "create_engine", lambda _url: engine)


class TestAvatarProviderRegistry:
    def test_get_default_provider_returns_mock(self):
        provider = get_avatar_provider("mock")
        assert provider.provider_name == "mock"

    def test_unknown_provider_raises(self):
        try:
            get_avatar_provider("unknown-provider")
            assert False, "Expected ValueError for unknown provider"
        except ValueError as exc:
            assert "Unsupported avatar provider" in str(exc)


class TestAvatarGenerationTaskFoundation:
    def _seed_draft(self, test_db, test_user):
        twin = test_db.query(Twin).filter(Twin.user_id == test_user.id).first()
        if not twin:
            twin = Twin(user_id=test_user.id, status="active")
            test_db.add(twin)
            test_db.flush()

        message = MessageService.create_message(
            test_db,
            test_user.id,
            "gmail",
            "sender-avatar-1",
            "Avatar Sender",
            "Please send this as avatar video",
            {},
        )

        draft = DraftService.create_draft(
            db=test_db,
            message_id=message.id,
            user_id=test_user.id,
            twin_id=twin.id,
            content="Thanks for reaching out.",
            confidence_score=0.88,
            confidence_label="High",
            moderation_passed=True,
            moderation_flags=[],
        )
        return draft

    def test_task_returns_disabled_when_feature_flag_off(self, test_db, test_user, monkeypatch):
        _bind_task_engine_to_test_db(monkeypatch, test_db)
        draft = self._seed_draft(test_db, test_user)

        class _Settings:
            feature_avatar_clone = False
            database_url = "sqlite://"

        monkeypatch.setattr(avatar_generation, "get_settings", lambda: _Settings())

        result = avatar_generation.generate_avatar.run(
            draft_id=draft.id,
            user_id=test_user.id,
            text="hello",
        )

        assert result["status"] == "disabled"

    def test_task_uses_profile_provider_and_updates_draft(self, test_db, test_user, monkeypatch):
        _bind_task_engine_to_test_db(monkeypatch, test_db)
        draft = self._seed_draft(test_db, test_user)

        profile = test_db.query(IdentityProfile).filter(IdentityProfile.user_id == test_user.id).first()
        if not profile:
            profile = IdentityProfile(user_id=test_user.id)
            test_db.add(profile)
        profile.avatar_provider = "mock"
        profile.avatar_model_id = "avatar-local-001"
        test_db.commit()

        class _Settings:
            feature_avatar_clone = True
            database_url = "sqlite://"
            avatar_provider = "mock"
            avatar_default_model_id = ""

        monkeypatch.setattr(avatar_generation, "get_settings", lambda: _Settings())

        result = avatar_generation.generate_avatar.run(
            draft_id=draft.id,
            user_id=test_user.id,
            text="hello",
        )

        assert result["status"] == "success"
        assert result["provider"] == "mock"
        assert result["avatar_status"] == "generated"
        assert result["video_url"].startswith("mock://avatar/")

        db = sessionmaker(bind=test_db.get_bind())()
        try:
            stored = db.query(Draft).filter(Draft.id == draft.id).first()
            assert stored.avatar_status == "generated"
            assert stored.avatar_provider == "mock"
            assert stored.avatar_model_id == "avatar-local-001"
            assert stored.avatar_video_url is not None
        finally:
            db.close()

    def test_task_returns_failed_when_provider_unconfigured(self, test_db, test_user, monkeypatch):
        _bind_task_engine_to_test_db(monkeypatch, test_db)
        draft = self._seed_draft(test_db, test_user)

        profile = test_db.query(IdentityProfile).filter(IdentityProfile.user_id == test_user.id).first()
        if not profile:
            profile = IdentityProfile(user_id=test_user.id)
            test_db.add(profile)
        profile.avatar_provider = "heygen"
        profile.avatar_model_id = "heygen-model"
        test_db.commit()

        class _Settings:
            feature_avatar_clone = True
            database_url = "sqlite://"
            avatar_provider = "heygen"
            avatar_default_model_id = ""
            heygen_api_key = ""

        monkeypatch.setattr(avatar_generation, "get_settings", lambda: _Settings())

        result = avatar_generation.generate_avatar.run(
            draft_id=draft.id,
            user_id=test_user.id,
            text="hello",
        )

        assert result["status"] == "failed"
        assert result["provider"] == "heygen"
        assert "not configured" in (result["error"] or "")
