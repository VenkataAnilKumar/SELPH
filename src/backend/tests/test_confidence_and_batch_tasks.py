"""Identity confidence uses learned evidence; batch voice/avatar jobs really fan out."""

from unittest.mock import patch

from app.models import Draft, Message
from app.services.identity import IdentityService
from app.tasks import avatar_generation as avatar_task
from app.tasks import voice_synthesis as voice_task


def _onboard(client, auth_headers):
    r = client.post(
        "/v1/identity/onboard",
        headers=auth_headers,
        json={
            "role": "creator", "communication_style": "friendly",
            "topics_avoided": ["politics"], "response_length": "short",
            "audience_tone": "warm", "three_words": ["a", "b", "c"],
        },
    )
    assert r.status_code == 201, r.text
    client.post("/v1/identity/topics/known", headers=auth_headers, json={"topic": "ai"})


def _make_drafts(db, user, twin_id, actions):
    ids = []
    for i, action in enumerate(actions):
        m = Message(user_id=user.id, channel="manual", sender_id=f"s{i}", sender_name="S", content="hi")
        db.add(m); db.commit()
        d = Draft(message_id=m.id, user_id=user.id, twin_id=twin_id, content=f"draft {i}", user_action=action)
        db.add(d); db.commit()
        ids.append(d.id)
    return ids


def test_confidence_equals_profile_score_without_decisions(client, auth_headers):
    _onboard(client, auth_headers)
    data = client.get("/v1/identity/confidence", headers=auth_headers).json()
    assert data["decisions"] == 0
    assert data["approval_quality"] is None
    assert data["score"] == data["profile_score"] == 1.0


def test_rejections_pull_confidence_down(client, auth_headers, test_db):
    from app.models import Twin, User
    _onboard(client, auth_headers)
    user = test_db.query(User).first()
    twin = test_db.query(Twin).filter(Twin.user_id == user.id).first()
    _make_drafts(test_db, user, twin.id, ["reject"] * 10 + ["edit"] * 10)

    data = client.get("/v1/identity/confidence", headers=auth_headers).json()
    assert data["decisions"] == 20 and data["rejected"] == 10 and data["edited"] == 10
    assert data["approval_quality"] == 0.25
    assert data["score"] < data["profile_score"]
    assert data["score"] == round(0.4 * 1.0 + 0.6 * 0.25, 2)
    assert data["label"] != "high"
    assert "editing or rejecting" in data["message"]


def test_approvals_keep_confidence_high(client, auth_headers, test_db):
    from app.models import Twin, User
    _onboard(client, auth_headers)
    user = test_db.query(User).first()
    twin = test_db.query(Twin).filter(Twin.user_id == user.id).first()
    _make_drafts(test_db, user, twin.id, ["approve"] * 20)
    data = client.get("/v1/identity/confidence", headers=auth_headers).json()
    assert data["score"] == 1.0 and data["label"] == "high"


def test_batch_voice_queues_only_owned_drafts(test_db, test_user, monkeypatch):
    from app.models import Twin
    twin = test_db.query(Twin).filter(Twin.user_id == test_user.id).first()
    ids = _make_drafts(test_db, test_user, twin.id, [None, None])
    engine = test_db.get_bind()
    monkeypatch.setattr(voice_task, "create_engine", lambda _url: engine)

    with patch.object(voice_task.synthesize_voice, "delay") as delay:
        result = voice_task.batch_synthesize_voices.run(ids + [ids[0], "missing-id"], test_user.id)

    assert result["status"] == "queued"
    assert result["queued"] == ids and result["skipped"] == ["missing-id"]
    assert delay.call_count == 2
    assert {c.kwargs["draft_id"] for c in delay.call_args_list} == set(ids)


def test_batch_voice_never_queues_another_users_draft(test_db, test_user, monkeypatch):
    from app.models import Twin
    twin = test_db.query(Twin).filter(Twin.user_id == test_user.id).first()
    ids = _make_drafts(test_db, test_user, twin.id, [None])
    monkeypatch.setattr(voice_task, "create_engine", lambda _url: test_db.get_bind())
    with patch.object(voice_task.synthesize_voice, "delay") as delay:
        result = voice_task.batch_synthesize_voices.run(ids, "someone-else")
    assert delay.call_count == 0 and result["skipped"] == ids


def test_batch_avatar_queues_owned_drafts(test_db, test_user, monkeypatch):
    from app.models import Twin
    twin = test_db.query(Twin).filter(Twin.user_id == test_user.id).first()
    ids = _make_drafts(test_db, test_user, twin.id, [None])
    monkeypatch.setattr(avatar_task, "create_engine", lambda _url: test_db.get_bind())
    with patch.object(avatar_task.generate_avatar, "delay") as delay:
        result = avatar_task.batch_generate_avatars.run(ids, test_user.id)
    assert result["queued"] == ids and delay.call_count == 1
