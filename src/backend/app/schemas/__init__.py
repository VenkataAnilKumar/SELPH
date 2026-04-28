"""
Pydantic schemas for API requests/responses
"""

from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    AuthResponse,
    PushTokenRequest,
    PushTokenResponse,
)

from app.schemas.twin import (
    TwinResponse,
    TwinStatsResponse,
    UpdateTwinRequest,
    MessageResponse,
    DraftResponse,
    DraftApprovalRequest,
)

from app.schemas.identity import (
    OnboardingRequest,
    OnboardingResponse,
    TopicRequest,
    TopicResponse,
    IdentityProfileResponse,
    UpdateIdentityRequest,
    IdentityConfidenceResponse,
)

__all__ = [
    # Auth
    "SignupRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "AuthResponse",
    "PushTokenRequest",
    "PushTokenResponse",
    # Twin
    "TwinResponse",
    "TwinStatsResponse",
    "UpdateTwinRequest",
    # Messages & Drafts
    "MessageResponse",
    "DraftResponse",
    "DraftApprovalRequest",
    # Identity
    "OnboardingRequest",
    "OnboardingResponse",
    "TopicRequest",
    "TopicResponse",
    "IdentityProfileResponse",
    "UpdateIdentityRequest",
    "IdentityConfidenceResponse",
]
