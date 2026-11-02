"""Configuration: the documented .env.example must actually load, and list settings take CSV or JSON."""

from pathlib import Path

import pytest

from app.config import Settings

BACKEND = Path(__file__).resolve().parent.parent


def test_env_example_loads_cleanly():
    """Regression: copying .env.example to .env used to crash startup (CORS_ORIGINS was not valid JSON)."""
    settings = Settings(_env_file=BACKEND / ".env.example")
    assert "http://localhost:3000" in settings.cors_origins
    assert "localhost" in settings.allowed_hosts
    assert isinstance(settings.cors_origins, list) and isinstance(settings.allowed_hosts, list)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("http://a.com,http://b.com", ["http://a.com", "http://b.com"]),
        (" http://a.com , http://b.com ,, ", ["http://a.com", "http://b.com"]),
        ('["http://a.com", "http://b.com"]', ["http://a.com", "http://b.com"]),
        ("http://only.com", ["http://only.com"]),
        ("", []),
    ],
)
def test_list_settings_accept_csv_and_json(monkeypatch, raw, expected):
    monkeypatch.setenv("CORS_ORIGINS", raw)
    monkeypatch.setenv("ALLOWED_HOSTS", raw)
    settings = Settings(_env_file=None)
    assert settings.cors_origins == expected
    assert settings.allowed_hosts == expected


def test_defaults_are_unchanged(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    settings = Settings(_env_file=None)
    assert "localhost" in settings.allowed_hosts and "testserver" in settings.allowed_hosts
    assert settings.cors_origins  # non-empty defaults still apply
