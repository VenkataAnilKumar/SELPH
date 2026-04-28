"""Phase 6 PR A tests: voice provider abstraction and task foundation."""

from unittest.mock import patch

from sqlalchemy.orm import sessionmaker

from app.models import Draft, IdentityProfile, Message, Twin
from app.services import MessageService, DraftService
from app.tasks import voice_synthesis
from app.voice.registry import get_voice_provider


def _bind_task_engine_to_test_db(monkeypatch, test_db):
    engine = test_db.get_bind()
    monkeypatch.setattr(voice_synthesis, "create_engine", lambda _url: engine)


class TestVoiceProviderRegistry:
    def test_get_default_provider_returns_mock(self):
        provider = get_voice_provider("mock")
        assert provider.provider_name == "mock"

    def test_unknown_provider_raises(self):
        try:
            get_voice_provider("unknown-provider")
            assert False, "Expected ValueError for unknown provider"
        except ValueError as exc:
            assert "Unsupported voice provider" in str(exc)


class TestVoiceSynthesisTaskFoundation:
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
            "sender-voice-1",
            "Voice Sender",
            "Please send this as voice",
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
            feature_voice_clone = False
            database_url = "sqlite://"

        monkeypatch.setattr(voice_synthesis, "get_settings", lambda: _Settings())

        result = voice_synthesis.synthesize_voice.run(
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
        profile.voice_provider = "mock"
        profile.voice_model_id = "model-local-001"
        test_db.commit()

        class _Settings:
            feature_voice_clone = True
            database_url = "sqlite://"
            voice_provider = "mock"
            voice_default_model_id = ""

        monkeypatch.setattr(voice_synthesis, "get_settings", lambda: _Settings())

        result = voice_synthesis.synthesize_voice.run(
            draft_id=draft.id,
            user_id=test_user.id,
            text="hello",
        )

        assert result["status"] == "success"
        assert result["provider"] == "mock"
        assert result["voice_status"] == "generated"
        assert result["audio_url"].startswith("mock://voice/")

        db = sessionmaker(bind=test_db.get_bind())()
        try:
            stored = db.query(Draft).filter(Draft.id == draft.id).first()
            assert stored.voice_status == "generated"
            assert stored.voice_provider == "mock"
            assert stored.voice_model_id == "model-local-001"
            assert stored.voice_audio_url is not None
        finally:
            db.close()

    def test_task_returns_failed_when_provider_unconfigured(self, test_db, test_user, monkeypatch):
        _bind_task_engine_to_test_db(monkeypatch, test_db)
        draft = self._seed_draft(test_db, test_user)

        profile = test_db.query(IdentityProfile).filter(IdentityProfile.user_id == test_user.id).first()
        if not profile:
            profile = IdentityProfile(user_id=test_user.id)
            test_db.add(profile)
        profile.voice_provider = "elevenlabs"
        profile.voice_model_id = "elv-model"
        test_db.commit()

        class _Settings:
            feature_voice_clone = True
            database_url = "sqlite://"
            voice_provider = "elevenlabs"
            voice_default_model_id = ""
            elevenlabs_api_key = ""

        monkeypatch.setattr(voice_synthesis, "get_settings", lambda: _Settings())

        result = voice_synthesis.synthesize_voice.run(
            draft_id=draft.id,
            user_id=test_user.id,
            text="hello",
        )

        assert result["status"] == "failed"
        assert result["provider"] == "elevenlabs"
        assert "not configured" in (result["error"] or "")
