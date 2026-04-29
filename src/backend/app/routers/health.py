"""
Health check endpoints
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, UTC
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db

router = APIRouter()


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
    checks = {}

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

    checks["jwt_secret"] = {"ok": jwt_secret_ok}
    if jwt_reason:
        checks["jwt_secret"]["reason"] = jwt_reason

    is_ready = all(item["ok"] for item in checks.values())
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }

    return JSONResponse(
        status_code=200 if is_ready else 503,
        content=payload,
    )
