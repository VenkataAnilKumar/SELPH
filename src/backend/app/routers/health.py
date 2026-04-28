"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "selph-backend",
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint (database connectivity, dependencies, etc.)
    """
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
    }
