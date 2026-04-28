"""
Integration tests for Phase 2 message -> draft pipeline tasks.
"""

from sqlalchemy.orm import sessionmaker

from app.models import Draft, Message
from app.services.message import MessageService
from app.services.identity import IdentityService
from app.tasks import draft_generation as draft_generation_task


def _bind_task_engine_to_test_db(monkeypatch, test_db):
    """Make task-level create_engine reuse the in-memory test database engine."""
    engine = test_db.get_bind()
    monkeypatch.setattr(draft_generation_task, "create_engine", lambda _url: engine)


class TestDraftGenerationTaskPipeline:
    def test_generate_draft_task_persists_draft_and_marks_message_ready(self, test_db, test_user, monkeypatch):
        """Task should create a draft row and set message status to draft_ready."""
        _bind_task_engine_to_test_db(monkeypatch, test_db)

        message = MessageService.create_message(
            test_db,
            test_user.id,
            "instagram_dm",
            "sender_task_1",
            "Alex",
            "Can you help with my content calendar?",
            {},
        )

        result = draft_generation_task.generate_draft_for_message.run(message.id, test_user.id)

        assert result["status"] == "success"
        assert result["draft_id"]
        assert result["generation_source"] in ["deterministic", "llm"]
        assert "pipeline_latency_ms" in result["metrics"]

        db = sessionmaker(bind=test_db.get_bind())()
        try:
            stored_message = db.query(Message).filter(Message.id == message.id).first()
            stored_draft = db.query(Draft).filter(Draft.id == result["draft_id"]).first()

            assert stored_message is not None
            assert stored_message.status == "draft_ready"
            assert stored_draft is not None
            assert stored_draft.message_id == message.id
            assert stored_draft.user_id == test_user.id
            assert stored_draft.content
            assert stored_draft.generation_source in ["deterministic", "llm"]
            assert stored_draft.estimated_total_tokens is not None
            assert stored_draft.estimated_cost_usd is not None
        finally:
            db.close()

    def test_generate_draft_task_uses_avoided_topic_fallback(self, test_db, test_user, monkeypatch):
        """Avoided topics should route task output through deterministic fallback guardrail."""
        _bind_task_engine_to_test_db(monkeypatch, test_db)

        IdentityService.add_avoided_topic(test_db, test_user.id, "politics")

        message = MessageService.create_message(
            test_db,
            test_user.id,
            "instagram_dm",
            "sender_task_2",
            "Jordan",
            "What is your opinion on politics right now?",
            {},
        )

        result = draft_generation_task.generate_draft_for_message.run(message.id, test_user.id)

        assert result["status"] == "success"

        db = sessionmaker(bind=test_db.get_bind())()
        try:
            draft = db.query(Draft).filter(Draft.id == result["draft_id"]).first()
            assert draft is not None
            assert "That's not something I cover" in draft.content
            assert draft.moderation_passed is True
        finally:
            db.close()

    def test_generate_draft_task_handles_missing_message(self, test_db, test_user, monkeypatch):
        """Task should return a non-raising error payload for unknown message IDs."""
        _bind_task_engine_to_test_db(monkeypatch, test_db)

        result = draft_generation_task.generate_draft_for_message.run("missing-message", test_user.id)

        assert result["status"] == "error"
        assert result["reason"] == "Message not found"
