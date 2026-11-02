"""Approving a draft delivers the reply: safely, once, and only when appropriate."""

import json
from unittest.mock import patch

import pytest
from celery.exceptions import Retry

from app.config import get_settings
from app.models import Draft, Message, Twin
from app.services.channel import ChannelService
from app.services.draft import DraftService
from app.tasks import send_reply as send_task

SEND = "app.tasks.send_reply.send_channel_reply.delay"


def _draft(db, user, *, channel="gmail", passed=True, status="pending_approval", connect=True):
    twin = db.query(Twin).filter(Twin.user_id == user.id).first()
    msg = Message(user_id=user.id, channel=channel, sender_id="a@b.com", sender_name="A", content="hi")
    db.add(msg); db.commit()
    draft = Draft(
        message_id=msg.id, user_id=user.id, twin_id=twin.id, content="reply",
        moderation_passed=passed, status=status,
    )
    db.add(draft); db.commit()
    if connect:
        ChannelService.upsert_credential(db, user.id, channel, json.dumps({"access_token": "x"}))
    return draft


def test_approve_queues_delivery_once(test_db, test_user):
    draft = _draft(test_db, test_user)
    with patch(SEND) as send:
        DraftService.approve_draft(test_db, draft.id, test_user.id)
    send.assert_called_once_with(draft.id)


def test_edit_also_queues_delivery(test_db, test_user):
    draft = _draft(test_db, test_user)
    with patch(SEND) as send:
        DraftService.edit_draft(test_db, draft.id, test_user.id, "my own words")
    send.assert_called_once_with(draft.id)


def test_reject_and_skip_never_deliver(test_db, test_user):
    a, b = _draft(test_db, test_user), _draft(test_db, test_user)
    with patch(SEND) as send:
        DraftService.reject_draft(test_db, a.id, test_user.id)
        DraftService.skip_draft(test_db, b.id, test_user.id)
    send.assert_not_called()


def test_no_connected_account_means_nothing_is_sent(test_db, test_user):
    """Simulated / manual messages have no channel account, so approving them delivers nowhere."""
    draft = _draft(test_db, test_user, channel="manual", connect=False)
    with patch(SEND) as send:
        result = DraftService.approve_draft(test_db, draft.id, test_user.id)
    send.assert_not_called()
    assert result.status == "approved"


def test_flagged_draft_is_not_auto_delivered(test_db, test_user):
    draft = _draft(test_db, test_user, passed=False)
    with patch(SEND) as send:
        result = DraftService.approve_draft(test_db, draft.id, test_user.id)
    send.assert_not_called()
    assert result.status == "approved"  # still approved; explicit /channels/send-reply is the opt-in


def test_auto_send_can_be_disabled(test_db, test_user, monkeypatch):
    monkeypatch.setattr(get_settings(), "auto_send_on_approve", False)
    draft = _draft(test_db, test_user)
    with patch(SEND) as send:
        DraftService.approve_draft(test_db, draft.id, test_user.id)
    send.assert_not_called()


def test_broker_outage_does_not_break_approval(test_db, test_user):
    draft = _draft(test_db, test_user)
    with patch(SEND, side_effect=ConnectionError("broker down")):
        result = DraftService.approve_draft(test_db, draft.id, test_user.id)
    assert result.status == "approved"  # decision recorded; retry via /channels/send-reply


# ── exactly once ─────────────────────────────────────────────────────────────

def test_second_decision_is_refused_and_does_not_redeliver(test_db, test_user):
    draft = _draft(test_db, test_user)
    with patch(SEND) as send:
        DraftService.approve_draft(test_db, draft.id, test_user.id)
        with pytest.raises(ValueError, match="already approved"):
            DraftService.approve_draft(test_db, draft.id, test_user.id)
        with pytest.raises(ValueError):
            DraftService.edit_draft(test_db, draft.id, test_user.id, "changed my mind")
    assert send.call_count == 1


def test_sent_draft_cannot_be_reapproved(test_db, test_user):
    draft = _draft(test_db, test_user, status="sent")
    with patch(SEND) as send:
        with pytest.raises(ValueError, match="already sent"):
            DraftService.approve_draft(test_db, draft.id, test_user.id)
    send.assert_not_called()


def test_simultaneous_decisions_only_one_wins(test_db, test_user):
    """Two requests that both read 'pending' (double-click): the conditional UPDATE lets one through."""
    draft = _draft(test_db, test_user)
    stale_copy = test_db.query(Draft).filter(Draft.id == draft.id).first()
    DraftService._claim_pending(test_db, draft, "approved")
    with pytest.raises(ValueError):
        DraftService._claim_pending(test_db, stale_copy, "approved")


def test_http_double_submit_delivers_once(client, auth_headers, test_db):
    from app.models import User

    user = test_db.query(User).first()
    draft = _draft(test_db, user)
    with patch(SEND) as send:
        first = client.post(f"/v1/drafts/{draft.id}/approve", headers=auth_headers, json={"action": "approve"})
        second = client.post(f"/v1/drafts/{draft.id}/approve", headers=auth_headers, json={"action": "approve"})
    assert first.status_code == 200 and second.status_code == 400
    assert send.call_count == 1


# ── the delivery task ────────────────────────────────────────────────────────

def _run_task(monkeypatch, test_db, draft_id):
    monkeypatch.setattr(send_task, "create_engine", lambda _url: test_db.get_bind())
    return send_task.send_channel_reply.run(draft_id)


def test_task_sends_and_marks_sent(test_db, test_user, monkeypatch):
    from unittest.mock import MagicMock

    draft = _draft(test_db, test_user, status="approved")
    adapter = MagicMock(); adapter.send_reply.return_value = True
    with patch("app.services.channel.get_adapter", return_value=adapter):
        result = _run_task(monkeypatch, test_db, draft.id)
    assert result["status"] == "sent"
    test_db.refresh(draft)
    assert draft.status == "sent" and draft.sent_response == "reply"


def test_task_retries_when_the_channel_call_fails(test_db, test_user, monkeypatch):
    from unittest.mock import MagicMock

    draft = _draft(test_db, test_user, status="approved")
    adapter = MagicMock(); adapter.send_reply.return_value = False  # e.g. rate limited / API down
    with patch("app.services.channel.get_adapter", return_value=adapter):
        with pytest.raises((Retry, RuntimeError)):
            _run_task(monkeypatch, test_db, draft.id)
    test_db.refresh(draft)
    assert draft.status == "send_failed"  # retryable via the task or /channels/send-reply


def test_task_does_not_retry_final_failures(test_db, test_user, monkeypatch):
    unapproved = _draft(test_db, test_user, status="pending_approval")
    assert _run_task(monkeypatch, test_db, unapproved.id)["status"] == "skipped"  # never sends, never retries

    no_account = _draft(test_db, test_user, channel="manual", status="approved", connect=False)
    assert _run_task(monkeypatch, test_db, no_account.id)["status"] == "skipped"
