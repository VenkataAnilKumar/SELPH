"""
Authentication endpoints
/v1/auth/*
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import SignupRequest, LoginRequest, TokenResponse, AuthResponse, UserResponse, PushTokenRequest, PushTokenResponse
from app.services import AuthService
from app.models import User

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
):
    """
    Sign up a new user with email and password
    
    Returns: User data and JWT tokens (access + refresh)
    """
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
    db: Session = Depends(get_db),
):
    """
    Log in user with email and password

    Returns: User data and JWT tokens (access + refresh)
    """
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
    current_user: User = Depends(get_current_user),
):
    """
    Refresh access token using current user's session
    
    Returns: New access token
    """
    access_token, refresh_token, expires_in = AuthService.generate_tokens(current_user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Logout user (placeholder - in production, implement token blacklist)
    
    Returns: Success message
    """
    # In production, add token to blacklist (Redis)
    # For now, just return success - token will expire naturally
    
    from app.models import AuditLog
    
    audit_log = AuditLog(
        user_id=current_user.id,
        action="logout",
        resource_type="User",
        resource_id=current_user.id,
        details={},
    )
    db.add(audit_log)
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

