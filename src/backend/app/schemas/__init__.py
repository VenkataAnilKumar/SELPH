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
    DraftVoiceGenerateRequest,
    DraftVoiceGenerateResponse,
    DraftVoiceStatusResponse,
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

from app.schemas.channels import (
    ChannelConnectRequest,
    ChannelConnectResponse,
    ConnectedChannelResponse,
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
    "DraftVoiceGenerateRequest",
    "DraftVoiceGenerateResponse",
    "DraftVoiceStatusResponse",
    # Identity
    "OnboardingRequest",
    "OnboardingResponse",
    "TopicRequest",
    "TopicResponse",
    "IdentityProfileResponse",
    "UpdateIdentityRequest",
    "IdentityConfidenceResponse",
    # Channels
    "ChannelConnectRequest",
    "ChannelConnectResponse",
    "ConnectedChannelResponse",
]
