"""Right to erasure and portability: complete, scoped, atomic, and provable."""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import func, select

from app.models import Base, DeletionCertificate, ReferralInvite, User
from app.services import erasure
from app.services.channel import ChannelService

PASSWORD = "Str0ngPass!234"
CONFIRM = "DELETE MY ACCOUNT"


def _signup(client, email):
    r = client.post("/v1/auth/signup", json={"email": email, "password": PASSWORD, "name": email.split("@")[0]})
    assert r.status_code == 201, r.text
    body = r.json()
    return body["user"]["id"], {"Authorization": f"Bearer {body['tokens']['access_token']}"}


def _populate(client, db, user_id, headers, tag):
    """Touch every kind of data a real user accumulates."""
    j = lambda r: (r.status_code < 300 or pytest.fail(r.text), r)[1]  # noqa: E731
    j(client.post("/v1/identity/onboard", headers=headers, json={
        "role": f"creator {tag}", "communication_style": "friendly", "topics_avoided": ["politics"],
        "response_length": "short", "audience_tone": "warm", "three_words": ["a", "b", "c"],
    }))
    j(client.post("/v1/identity/topics/known", headers=headers, json={"topic": f"topic-{tag}"}))
    j(client.post("/v1/identity/briefings", headers=headers, json={
        "briefing_type": "instruction", "topic": "t", "content": f"secret-briefing-{tag}", "priority": 5}))
    j(client.put("/v1/identity/sender-tiers", headers=headers, json={"sender_id": f"vip-{tag}", "platform": "gmail", "tier": 0}))
    j(client.post("/v1/identity/voice/consent", headers=headers, json={"granted": True}))
    j(client.post("/v1/identity/profiles", headers=headers, json={"profile_name": f"p-{tag}", "tone": "warm"})) if False else None

    ids = []
    for i in range(6):
        r = j(client.post("/v1/messages/ingest", headers=headers, json={
            "channel": "instagram_dm", "sender_id": f"s{i}", "sender_name": f"S{i}",
            "content": f"What tools do you use? ({tag})"}))
        ids.append(r.json()["draft_id"])
    j(client.post(f"/v1/drafts/{ids[0]}/approve", headers=headers, json={"action": "approve"}))   # issues certificate
    j(client.post(f"/v1/drafts/{ids[1]}/approve", headers=headers, json={"action": "edit", "edited_content": f"edited-{tag}"}))
    clusters = j(client.post("/v1/drafts/batches/cluster", headers=headers, json={})).json()
    for c in clusters["items"]:
        j(client.post(f"/v1/drafts/batches/{c['id']}/approve", headers=headers, json={"template_approved": "Hi {sender_name}"}))

    ChannelService.upsert_credential(db, user_id, "gmail", json.dumps({"access_token": f"TOKEN-{tag}"}), scope="{}")
    db.add(ReferralInvite(referrer_user_id=user_id, invitee_email=f"x-{tag}@example.com", referral_code=f"CODE-{tag}"))
    db.commit()


def _user_scoped_counts(db, user_id):
    counts = {}
    for table in Base.metadata.sorted_tables:
        if table.name in ("deletion_certificates", "users"):
            continue
        cond = erasure._scope(db, table, user_id)
        if cond is None:
            continue
        counts[table.name] = db.execute(select(func.count()).select_from(table).where(cond)).scalar()
    return {k: v for k, v in counts.items() if v}


@pytest.fixture
def two_users(client, test_db):
    a_id, a_headers = _signup(client, "alice@example.com")
    b_id, b_headers = _signup(client, "bob@example.com")
    _populate(client, test_db, a_id, a_headers, "A")
    _populate(client, test_db, b_id, b_headers, "B")
    return {"a": (a_id, a_headers), "b": (b_id, b_headers)}


def _delete(client, headers, **over):
    body = {"password": PASSWORD, "confirm": CONFIRM, **over}
    return client.request("DELETE", "/v1/privacy/account", headers=headers, json=body)


# ── completeness and scoping ─────────────────────────────────────────────────

def test_populated_user_really_spans_many_tables(two_users, test_db):
    a_id = two_users["a"][0]
    tables = set(_user_scoped_counts(test_db, a_id))
    required = {"messages", "drafts", "twins", "topics", "twin_briefings", "sender_tiers", "consents",
                "channel_credentials", "twin_certificates", "message_clusters", "batch_sends",
                "referral_invites", "audit_logs"}
    assert required <= tables, f"fixture does not populate: {sorted(required - tables)}"


def test_erase_removes_every_row_of_the_user_and_nothing_of_others(client, test_db, two_users):
    a_id, a_headers = two_users["a"]
    b_id, _ = two_users["b"]
    b_before = _user_scoped_counts(test_db, b_id)
    users_before = test_db.query(User).count()

    r = _delete(client, a_headers)
    assert r.status_code == 200, r.text

    assert _user_scoped_counts(test_db, a_id) == {}                      # nothing left, in any table
    assert test_db.get(User, a_id) is None
    assert _user_scoped_counts(test_db, b_id) == b_before                # other user untouched
    assert test_db.query(User).count() == users_before - 1 + 1           # -alice, +tombstone
    leaked = test_db.execute(select(func.count()).select_from(Base.metadata.tables["channel_credentials"])).scalar()
    assert leaked == 1  # only bob's


def test_audit_logs_are_retained_but_anonymized(client, test_db, two_users):
    a_id, a_headers = two_users["a"]
    audit = Base.metadata.tables["audit_logs"]
    mine = test_db.execute(select(func.count()).select_from(audit).where(audit.c.user_id == a_id)).scalar()
    assert mine > 0

    _delete(client, a_headers)

    assert test_db.execute(select(func.count()).select_from(audit).where(audit.c.user_id == a_id)).scalar() == 0
    kept = test_db.execute(select(audit).where(audit.c.user_id == erasure.TOMBSTONE_USER_ID)).mappings().all()
    assert len(kept) == mine                                              # retained, not dropped
    assert all(row["details"] == {} and row["resource_id"] is None and row["ip_address"] is None for row in kept)
    assert all(row["action"] for row in kept)                             # what happened is still known


def test_referral_rows_of_other_users_survive_with_the_link_removed(client, test_db, two_users):
    a_id, a_headers = two_users["a"]
    b_id, _ = two_users["b"]
    test_db.add(ReferralInvite(referrer_user_id=b_id, invitee_user_id=a_id, invitee_email="alice@example.com", referral_code="B-INVITED-A"))
    test_db.commit()

    _delete(client, a_headers)

    row = test_db.query(ReferralInvite).filter(ReferralInvite.referral_code == "B-INVITED-A").one()
    assert row.referrer_user_id == b_id and row.invitee_user_id is None


# ── safety rails ─────────────────────────────────────────────────────────────

def test_wrong_password_or_confirmation_deletes_nothing(client, test_db, two_users):
    a_id, a_headers = two_users["a"]
    before = _user_scoped_counts(test_db, a_id)

    assert _delete(client, a_headers, password="WrongPass123!").status_code == 403
    assert _delete(client, a_headers, confirm="delete my account").status_code == 400
    assert _delete(client, a_headers, confirm="").status_code == 400
    assert client.request("DELETE", "/v1/privacy/account", headers=a_headers, json={"password": PASSWORD}).status_code == 422

    assert _user_scoped_counts(test_db, a_id) == before
    assert test_db.get(User, a_id) is not None


def test_requires_authentication(client):
    assert client.request("DELETE", "/v1/privacy/account", json={"password": PASSWORD, "confirm": CONFIRM}).status_code in (401, 403)
    assert client.get("/v1/privacy/export").status_code in (401, 403)


def test_failure_midway_rolls_everything_back(client, test_db, two_users):
    a_id, a_headers = two_users["a"]
    before = _user_scoped_counts(test_db, a_id)

    with patch.object(erasure, "DeletionCertificate", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            client.request("DELETE", "/v1/privacy/account", headers=a_headers, json={"password": PASSWORD, "confirm": CONFIRM})

    assert test_db.get(User, a_id) is not None                           # user still there
    assert _user_scoped_counts(test_db, a_id) == before                  # and every row, intact
    assert test_db.query(DeletionCertificate).count() == 0               # and no false certificate


def test_session_is_dead_and_login_fails_after_erasure(client, two_users):
    _, a_headers = two_users["a"]
    _delete(client, a_headers)
    assert client.get("/v1/auth/me", headers=a_headers).status_code == 401
    login = client.post("/v1/auth/login", json={"email": "alice@example.com", "password": PASSWORD})
    assert login.status_code in (400, 401)


def test_tombstone_cannot_log_in_or_be_erased(client, test_db, two_users):
    _delete(client, two_users["a"][1])
    for pw in ("!", "", PASSWORD):
        r = client.post("/v1/auth/login", json={"email": erasure.TOMBSTONE_EMAIL, "password": pw or "x"})
        assert r.status_code in (400, 401, 422)
    with pytest.raises(ValueError):
        erasure.erase_user(test_db, erasure.TOMBSTONE_USER_ID)


# ── the certificate ──────────────────────────────────────────────────────────

def test_certificate_is_verifiable_and_tamper_evident(client, test_db, two_users):
    a_id, a_headers = two_users["a"]
    cert = _delete(client, a_headers).json()
    assert cert["valid"] is True
    assert cert["summary"]["tables"]["users"] == 1 and cert["summary"]["tables"]["messages"] >= 3
    assert any("providers" in n for n in cert["summary"]["notes"])        # honest about what we cannot delete

    public = client.get(f"/v1/privacy/deletion-certificates/{cert['certificate_id']}")      # no auth needed
    assert public.status_code == 200 and public.json()["valid"] is True
    assert a_id not in json.dumps(public.json())                                              # nothing identifying

    # the former user can prove it was theirs; nobody else can link it to them
    assert cert["subject_hash"] == erasure.subject_hash_for(a_id, cert["certificate_id"])
    assert cert["subject_hash"] != erasure.subject_hash_for("someone-else", cert["certificate_id"])

    row = test_db.get(DeletionCertificate, cert["certificate_id"])
    row.summary = {**row.summary, "tables": {"users": 0}}                 # tamper with the record
    test_db.commit()
    assert client.get(f"/v1/privacy/deletion-certificates/{cert['certificate_id']}").json()["valid"] is False


def test_unknown_certificate_is_404(client):
    assert client.get("/v1/privacy/deletion-certificates/nope").status_code == 404


# ── portability ──────────────────────────────────────────────────────────────

def test_export_contains_own_data_and_no_secrets(client, two_users):
    _, a_headers = two_users["a"]
    r = client.get("/v1/privacy/export", headers=a_headers)
    assert r.status_code == 200
    body = r.json()
    text = json.dumps(body["data"])  # the "excluded" label list legitimately names the omitted columns

    assert body["format"] == "selph-export-v1"
    assert {"users", "messages", "drafts", "topics", "twin_briefings"} <= set(body["data"])
    assert "secret-briefing-A" in text and "edited-A" in text            # their content is there
    assert "secret-briefing-B" not in text and "bob@example.com" not in text   # other users' is not
    for secret in ("password_hash", "credential_value", "private_key_ref", "push_token", "TOKEN-A", PASSWORD):
        assert secret not in text
    assert "revoked_tokens" not in body["data"]
