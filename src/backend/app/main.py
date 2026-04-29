"""
SELPH Backend API
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.models import Base  # Import models to register with SQLAlchemy
from app.routers import (
    auth,
    twin,
    messages,
    drafts,
    channels,
    health,
    identity,
    referrals,
    proactive,
    crisis,
    style,
    verification,
    privacy,
    t2t,
)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("🚀 SELPH Backend Starting...")
    print(f"   Environment: {settings.environment}")
    print(f"   API Version: {settings.api_v1_str}")

    if settings.environment.lower() == "production" and settings.enforce_production_jwt_secret:
        # Block unsafe default/weak JWT secrets in production.
        if settings.jwt_secret_key == "dev-secret-key-change-in-production" or len(settings.jwt_secret_key) < 32:
            raise RuntimeError("Insecure JWT secret for production. Set JWT_SECRET_KEY to a strong 32+ char value.")
    
    yield
    
    # Shutdown
    print("👋 SELPH Backend Shutting Down...")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    """
    app = FastAPI(
        title=settings.api_title,
        description="Your Digital Twin AI",
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # Middleware: CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Middleware: Trusted hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts,
    )
    
    # Include routers
    app.include_router(
        health.router,
        tags=["Health"],
    )
    
    app.include_router(
        auth.router,
        prefix=f"{settings.api_v1_str}/auth",
        tags=["Authentication"],
    )
    
    app.include_router(
        twin.router,
        prefix=f"{settings.api_v1_str}/twin",
        tags=["Twin"],
    )
    
    app.include_router(
        messages.router,
        prefix=f"{settings.api_v1_str}/messages",
        tags=["Messages"],
    )
    
    app.include_router(
        drafts.router,
        prefix=f"{settings.api_v1_str}/drafts",
        tags=["Drafts"],
    )
    
    app.include_router(
        channels.router,
        prefix=f"{settings.api_v1_str}/channels",
        tags=["Channels"],
    )

    app.include_router(
        identity.router,
        prefix=f"{settings.api_v1_str}/identity",
        tags=["Identity"],
    )

    app.include_router(
        referrals.router,
        prefix=f"{settings.api_v1_str}/referrals",
        tags=["Referrals"],
    )

    app.include_router(
        proactive.router,
        prefix=f"{settings.api_v1_str}/proactive",
        tags=["Proactive"],
    )

    app.include_router(
        crisis.router,
        prefix=f"{settings.api_v1_str}/twin",
        tags=["Crisis"],
    )

    app.include_router(
        style.router,
        prefix=f"{settings.api_v1_str}/twin",
        tags=["Style"],
    )

    app.include_router(
        verification.router,
        tags=["Verification"],
    )

    app.include_router(
        privacy.router,
        prefix=f"{settings.api_v1_str}/privacy",
        tags=["Privacy"],
    )

    app.include_router(
        t2t.router,
        prefix=f"{settings.api_v1_str}/t2t",
        tags=["T2T"],
    )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
