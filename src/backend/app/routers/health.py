"""
Health check endpoints
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
import hmac
from datetime import datetime, UTC
from typing import Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db

router = APIRouter()


def _has_value(value) -> bool:
    return bool(value and str(value).strip())


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "selph-backend",
    }


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check endpoint (database connectivity, dependencies, etc.)
    """
    settings = get_settings()
    checks: dict[str, dict[str, Any]] = {}

    # Database dependency probe.
    try:
        # Use a minimal query compatible with SQLite/PostgreSQL.
        db.execute(text("SELECT 1"))
        checks["database"] = {"ok": True}
    except Exception as exc:
        checks["database"] = {"ok": False, "reason": str(exc)}

    jwt_secret_ok = True
    jwt_reason = None
    if settings.environment.lower() == "production" and settings.enforce_production_jwt_secret:
        if settings.jwt_secret_key == "dev-secret-key-change-in-production" or len(settings.jwt_secret_key) < 32:
            jwt_secret_ok = False
            jwt_reason = "Insecure JWT secret for production"

    cred_ok, cred_reason = True, None
    if settings.environment.lower() == "production" and not _has_value(settings.credential_encryption_key):
        cred_ok, cred_reason = False, "CREDENTIAL_ENCRYPTION_KEY is required in production"
    checks["credential_encryption"] = {"ok": cred_ok}
    if cred_reason:
        checks["credential_encryption"]["reason"] = cred_reason

    webhook_problems = []
    if settings.feature_instagram and not _has_value(settings.meta_app_secret):
        webhook_problems.append("META_APP_SECRET missing: Instagram webhooks are rejected")
    if settings.feature_gmail and not _has_value(settings.google_webhook_secret):
        webhook_problems.append("GOOGLE_WEBHOOK_SECRET missing: Gmail webhooks are rejected")
    if settings.allow_unsigned_webhooks and settings.environment.lower() == "production":
        webhook_problems.append("ALLOW_UNSIGNED_WEBHOOKS is ignored in production")
    checks["webhook_security"] = {"ok": not webhook_problems}
    if webhook_problems:
        checks["webhook_security"]["reason"] = "; ".join(webhook_problems)

    checks["jwt_secret"] = {"ok": jwt_secret_ok}
    if jwt_reason:
        checks["jwt_secret"]["reason"] = jwt_reason

    instagram_ok = True
    instagram_reason = None
    if settings.feature_instagram:
        required_instagram = [
            settings.meta_app_id,
            settings.meta_app_secret,
            settings.meta_verify_token,
            settings.meta_oauth_redirect_uri,
        ]
        instagram_ok = all(_has_value(v) for v in required_instagram)
        if not instagram_ok:
            instagram_reason = "Instagram enabled but Meta OAuth/webhook settings are incomplete"
    checks["feature_instagram"] = {"ok": instagram_ok}
    if instagram_reason:
        checks["feature_instagram"]["reason"] = instagram_reason

    gmail_ok = True
    gmail_reason = None
    if settings.feature_gmail:
        required_gmail = [
            settings.google_oauth_client_id,
            settings.google_oauth_client_secret,
            settings.google_oauth_redirect_uri,
            settings.google_pubsub_topic,
        ]
        gmail_ok = all(_has_value(v) for v in required_gmail)
        if not gmail_ok:
            gmail_reason = "Gmail enabled but OAuth/PubSub settings are incomplete"
    checks["feature_gmail"] = {"ok": gmail_ok}
    if gmail_reason:
        checks["feature_gmail"]["reason"] = gmail_reason

    voice_provider_ok = True
    voice_provider_reason = None
    if settings.feature_voice_clone and settings.voice_provider == "elevenlabs":
        voice_provider_ok = _has_value(settings.elevenlabs_api_key)
        if not voice_provider_ok:
            voice_provider_reason = "Voice clone enabled with ElevenLabs but API key is missing"
    checks["feature_voice_clone"] = {"ok": voice_provider_ok}
    if voice_provider_reason:
        checks["feature_voice_clone"]["reason"] = voice_provider_reason

    avatar_provider_ok = True
    avatar_provider_reason = None
    if settings.feature_avatar_clone and settings.avatar_provider == "heygen":
        avatar_provider_ok = _has_value(settings.heygen_api_key)
        if not avatar_provider_ok:
            avatar_provider_reason = "Avatar clone enabled with HeyGen but API key is missing"
    checks["feature_avatar_clone"] = {"ok": avatar_provider_ok}
    if avatar_provider_reason:
        checks["feature_avatar_clone"]["reason"] = avatar_provider_reason

    is_ready = all(bool(item.get("ok")) for item in checks.values())
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }

    return JSONResponse(
        status_code=200 if is_ready else 503,
        content=payload,
    )


@router.get("/metrics", include_in_schema=False)
async def metrics(request: Request, db: Session = Depends(get_db)):
    """Prometheus scrape endpoint. Optionally protected by METRICS_TOKEN (Bearer)."""
    from fastapi import HTTPException
    from fastapi.responses import PlainTextResponse
    from app import metrics as app_metrics

    settings = get_settings()
    if not settings.enable_metrics:
        raise HTTPException(status_code=404, detail="Not found")
    if settings.metrics_token:
        supplied = request.headers.get("Authorization", "")
        expected = f"Bearer {settings.metrics_token}"
        if not hmac.compare_digest(supplied.encode("utf-8", "ignore"), expected.encode("utf-8")):
            raise HTTPException(status_code=401, detail="Metrics token required")
    elif settings.environment.lower() == "production":
        raise HTTPException(status_code=404, detail="Not found")  # never expose unauthenticated in production

    body = app_metrics.render_metrics(db=db, broker_url=settings.celery_broker_url)
    return PlainTextResponse(body, media_type="text/plain; version=0.0.4")
