"""Configured token lifetimes, and a rate limiter that holds across replicas."""

import time

import jwt
import pytest

from app import ratelimit
from app.config import get_settings


@pytest.fixture(autouse=True)
def _clean_limiter():
    ratelimit.reset()
    yield
    ratelimit.reset()


# ── token lifetimes honor configuration ──────────────────────────────────────

def _exp_in_seconds(token: str) -> float:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return payload["exp"] - time.time()


def test_token_lifetimes_come_from_settings(client, test_user_data, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "jwt_expiration_hours", 1)
    monkeypatch.setattr(settings, "jwt_refresh_expiration_days", 2)

    client.post("/v1/auth/signup", json=test_user_data)
    tokens = client.post(
        "/v1/auth/login", json={"email": test_user_data["email"], "password": test_user_data["password"]}
    ).json()["tokens"]

    assert 3500 < _exp_in_seconds(tokens["access_token"]) <= 3600
    assert 2 * 86400 - 100 < _exp_in_seconds(tokens["refresh_token"]) <= 2 * 86400
    assert tokens["expires_in"] == 3600


def test_default_lifetimes_unchanged(client, test_user_data):
    client.post("/v1/auth/signup", json=test_user_data)
    tokens = client.post(
        "/v1/auth/login", json={"email": test_user_data["email"], "password": test_user_data["password"]}
    ).json()["tokens"]
    assert tokens["expires_in"] == 86400
    assert 7 * 86400 - 100 < _exp_in_seconds(tokens["refresh_token"]) <= 7 * 86400


# ── rate limiter ─────────────────────────────────────────────────────────────

class FakeRedis:
    """Minimal INCR/EXPIRE stand-in shared between 'replicas'."""

    def __init__(self):
        self.data, self.expiries = {}, {}

    def incr(self, key):
        self.data[key] = self.data.get(key, 0) + 1
        return self.data[key]

    def expire(self, key, seconds):
        self.expiries[key] = seconds


def test_limit_is_shared_across_replicas_via_redis(monkeypatch):
    shared = FakeRedis()
    monkeypatch.setattr(ratelimit, "_redis", lambda: shared)

    # Two replicas see the same counter because the state is in Redis, not in-process.
    counts = [ratelimit.hit("login", "1.2.3.4", now=1000.0) for _ in range(5)]
    assert counts == [1, 2, 3, 4, 5]
    assert ratelimit._local == {}  # nothing kept in-process when Redis works
    assert list(shared.expiries.values()) == [120]  # keys expire on their own


def test_window_rolls_over_and_clients_are_isolated(monkeypatch):
    monkeypatch.setattr(ratelimit, "_redis", lambda: None)
    assert [ratelimit.hit("login", "a", now=1000.0) for _ in range(3)] == [1, 2, 3]
    assert ratelimit.hit("login", "b", now=1000.0) == 1           # other client unaffected
    assert ratelimit.hit("signup", "a", now=1000.0) == 1          # other route unaffected
    assert ratelimit.hit("login", "a", now=1000.0 + 61) == 1      # next minute starts fresh


def test_falls_back_to_local_counting_when_redis_errors(monkeypatch):
    class Broken:
        def incr(self, key):
            raise ConnectionError("redis down")

    monkeypatch.setattr(ratelimit, "_redis", lambda: Broken())
    assert [ratelimit.hit("login", "z", now=5000.0) for _ in range(3)] == [1, 2, 3]  # still limits
    assert ratelimit._redis_down_until > time.time()  # and backs off instead of retrying every call


def test_local_buckets_do_not_grow_without_bound(monkeypatch):
    monkeypatch.setattr(ratelimit, "_redis", lambda: None)
    for i in range(10_050):
        ratelimit.hit("login", f"ip-{i}", now=1000.0)
    ratelimit.hit("login", "later", now=1000.0 + 120)  # a later window triggers the sweep
    assert len(ratelimit._local) < 100


def test_login_is_throttled_in_production_with_retry_after(client, test_user_data, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "auth_rate_limit_per_minute", 3)
    monkeypatch.setattr(ratelimit, "_redis", lambda: None)
    body = {"email": "nobody@example.com", "password": "WrongPass123"}

    codes = [client.post("/v1/auth/login", json=body).status_code for _ in range(5)]
    assert codes[:3] == [401, 401, 401] or all(c in (400, 401) for c in codes[:3])
    assert codes[3:] == [429, 429]
    blocked = client.post("/v1/auth/login", json=body)
    assert blocked.headers["Retry-After"] == "60"


def test_refresh_with_token_body_is_throttled(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "auth_rate_limit_per_minute", 2)
    monkeypatch.setattr(ratelimit, "_redis", lambda: None)
    codes = [client.post("/v1/auth/refresh", json={"refresh_token": "junk"}).status_code for _ in range(4)]
    assert codes == [401, 401, 429, 429]


def test_not_throttled_outside_production(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "auth_rate_limit_per_minute", 1)
    monkeypatch.setattr(ratelimit, "_redis", lambda: None)
    body = {"email": "nobody@example.com", "password": "WrongPass123"}
    assert all(client.post("/v1/auth/login", json=body).status_code != 429 for _ in range(5))
