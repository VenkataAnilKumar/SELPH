"""Server-side logout, token typing and refresh rotation."""

from datetime import timedelta

from app.security import create_access_token, create_refresh_token


def _login(client, test_user_data):
    client.post("/v1/auth/signup", json=test_user_data)
    r = client.post(
        "/v1/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    assert r.status_code == 200, r.text
    return r.json()["tokens"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_logout_revokes_access_token_immediately(client, test_user_data):
    tokens = _login(client, test_user_data)
    assert client.get("/v1/auth/me", headers=_auth(tokens["access_token"])).status_code == 200

    assert client.post("/v1/auth/logout", headers=_auth(tokens["access_token"])).status_code == 200

    after = client.get("/v1/auth/me", headers=_auth(tokens["access_token"]))
    assert after.status_code == 401


def test_logout_is_idempotent_for_other_sessions(client, test_user_data):
    first = _login(client, test_user_data)
    second = _login(client, test_user_data)
    client.post("/v1/auth/logout", headers=_auth(first["access_token"]))
    # a different session of the same user keeps working
    assert client.get("/v1/auth/me", headers=_auth(second["access_token"])).status_code == 200


def test_refresh_token_cannot_be_used_as_bearer(client, test_user_data):
    tokens = _login(client, test_user_data)
    r = client.get("/v1/auth/me", headers=_auth(tokens["refresh_token"]))
    assert r.status_code == 401


def test_oauth_state_token_cannot_be_used_as_bearer(client, test_user_data, test_user):
    state, _ = create_access_token(
        data={"sub": test_user.id, "purpose": "channel_oauth_state"},
        expires_delta=timedelta(minutes=10),
    )
    assert client.get("/v1/auth/me", headers=_auth(state)).status_code == 401


def test_legacy_token_without_type_still_works(client, test_user_data, test_user):
    import jwt
    from app.config import settings
    from datetime import datetime, UTC

    legacy = jwt.encode(
        {"sub": test_user.id, "exp": datetime.now(UTC) + timedelta(hours=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert client.get("/v1/auth/me", headers=_auth(legacy)).status_code == 200
    # ...and can be revoked even though it has no jti
    assert client.post("/v1/auth/logout", headers=_auth(legacy)).status_code == 200
    assert client.get("/v1/auth/me", headers=_auth(legacy)).status_code == 401


def test_refresh_with_refresh_token_rotates_and_revokes_old(client, test_user_data):
    tokens = _login(client, test_user_data)
    r = client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200, r.text
    new = r.json()
    assert new["access_token"] != tokens["access_token"]
    assert client.get("/v1/auth/me", headers=_auth(new["access_token"])).status_code == 200

    # old refresh token is single-use
    replay = client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert replay.status_code == 401


def test_refresh_rejects_access_token_in_body_and_garbage(client, test_user_data):
    tokens = _login(client, test_user_data)
    assert client.post("/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}).status_code == 401
    assert client.post("/v1/auth/refresh", json={"refresh_token": "nope"}).status_code == 401


def test_refresh_without_body_requires_valid_bearer(client, test_user_data):
    tokens = _login(client, test_user_data)
    assert client.post("/v1/auth/refresh").status_code == 401
    ok = client.post("/v1/auth/refresh", headers=_auth(tokens["access_token"]))
    assert ok.status_code == 200


def test_logout_can_also_revoke_refresh_token(client, test_user_data):
    tokens = _login(client, test_user_data)
    client.post(
        "/v1/auth/logout",
        headers=_auth(tokens["access_token"]),
        json={"refresh_token": tokens["refresh_token"]},
    )
    r = client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


def test_refresh_token_of_inactive_or_foreign_user_rejected(client, test_user_data, test_user):
    forged = create_refresh_token({"sub": "no-such-user"})
    assert client.post("/v1/auth/refresh", json={"refresh_token": forged}).status_code == 401
