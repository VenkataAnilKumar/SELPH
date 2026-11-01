"""
Authentication endpoints
/v1/auth/*
"""

import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import (
    get_current_user,
    optional_security,
    resolve_user_from_access_token,
    security,
)
from app.security import verify_token
from app.services.token_revocation import TokenRevocationService
from app import ratelimit
from app.config import get_settings
from app.schemas.auth import RefreshRequest, LogoutRequest
from app.schemas import SignupRequest, LoginRequest, TokenResponse, AuthResponse, UserResponse, PushTokenRequest, PushTokenResponse
from app.services import AuthService
from app.models import User

router = APIRouter(tags=["auth"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _enforce_auth_rate_limit(route_name: str, client_ip: str) -> None:
    """Throttle credential endpoints per client IP (production only)."""
    settings = get_settings()
    if settings.environment.lower() != "production":
        return

    limit = max(1, settings.auth_rate_limit_per_minute)
    if ratelimit.hit(route_name, client_ip) > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please wait and try again.",
            headers={"Retry-After": "60"},
        )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    client_request: Request,
    db: Session = Depends(get_db),
):
    """
    Sign up a new user with email and password
    
    Returns: User data and JWT tokens (access + refresh)
    """
    _enforce_auth_rate_limit("signup", getattr(client_request.client, "host", "unknown"))

    try:
        user = AuthService.signup(db, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    access_token, refresh_token, expires_in = AuthService.generate_tokens(user.id)
    
    return {
        "user": UserResponse.model_validate(user),
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        },
    }


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    client_request: Request,
    db: Session = Depends(get_db),
):
    """
    Log in user with email and password

    Returns: User data and JWT tokens (access + refresh)
    """
    _enforce_auth_rate_limit("login", getattr(client_request.client, "host", "unknown"))

    try:
        user = AuthService.login(db, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    access_token, refresh_token, expires_in = AuthService.generate_tokens(user.id)

    return {
        "user": UserResponse.model_validate(user),
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        },
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    client_request: Request,
    request: Optional[RefreshRequest] = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db),
):
    """
    Issue a new token pair.

    - With `{"refresh_token": "..."}` in the body: validates the refresh token, rotates it
      (the old one is revoked) and works even when the access token has expired.
    - Without a body: requires a valid access token in the Authorization header.
    """
    if request and request.refresh_token:
        _enforce_auth_rate_limit("refresh", _client_ip(client_request))
        old = request.refresh_token
        payload = verify_token(old)
        invalid = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        if not payload or payload.get("type") != "refresh" or payload.get("purpose"):
            raise invalid
        if TokenRevocationService.is_revoked(db, old, payload):
            raise invalid
        user = AuthService.get_user_by_id(db, payload.get("sub", ""))
        if not user or not user.is_active:
            raise invalid
        TokenRevocationService.revoke(db, old, payload, user.id)
        user_id = user.id
    else:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = resolve_user_from_access_token(credentials.credentials, db).id

    access_token, refresh_token, expires_in = AuthService.generate_tokens(user_id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.post("/logout")
async def logout(
    request: Optional[LogoutRequest] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Log out: revoke the presented access token (and the refresh token if supplied).

    Revoked tokens are rejected immediately, server-side, until they would have expired.

    Returns: Success message
    """
    access_token = credentials.credentials
    TokenRevocationService.revoke(
        db, access_token, verify_token(access_token) or {}, current_user.id
    )

    if request and request.refresh_token:
        refresh_payload = verify_token(request.refresh_token)
        if (
            refresh_payload
            and refresh_payload.get("type") == "refresh"
            and refresh_payload.get("sub") == current_user.id
        ):
            TokenRevocationService.revoke(db, request.refresh_token, refresh_payload, current_user.id)

    TokenRevocationService.purge_expired(db)

    from app.models import AuditLog

    db.add(AuditLog(
        user_id=current_user.id,
        action="logout",
        resource_type="User",
        resource_id=current_user.id,
        details={"refresh_revoked": bool(request and request.refresh_token)},
    ))
    db.commit()

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user's profile
    
    Returns: User data
    """
    return UserResponse.model_validate(current_user)


@router.post("/push-token", response_model=PushTokenResponse)
async def register_push_token(
    request: PushTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register or update an Expo push token for the authenticated user.
    Called by the mobile app after obtaining an Expo push token.
    """
    current_user.push_token = request.token
    db.commit()
    return {"registered": True}

