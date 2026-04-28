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
    TwinQualitySummaryResponse,
    TwinWeeklyDigestResponse,
    UpdateTwinRequest,
    MessageResponse,
    DraftResponse,
    DraftApprovalRequest,
    DraftVoiceGenerateRequest,
    DraftVoiceGenerateResponse,
    DraftVoiceStatusResponse,
    DraftAvatarGenerateRequest,
    DraftAvatarGenerateResponse,
    DraftAvatarStatusResponse,
)

from app.schemas.identity import (
    OnboardingRequest,
    OnboardingResponse,
    TopicRequest,
    TopicResponse,
    IdentityProfileResponse,
    UpdateIdentityRequest,
    IdentityConfidenceResponse,
    IdentityOnboardingStatusResponse,
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
    "TwinQualitySummaryResponse",
    "TwinWeeklyDigestResponse",
    "UpdateTwinRequest",
    # Messages & Drafts
    "MessageResponse",
    "DraftResponse",
    "DraftApprovalRequest",
    "DraftVoiceGenerateRequest",
    "DraftVoiceGenerateResponse",
    "DraftVoiceStatusResponse",
    "DraftAvatarGenerateRequest",
    "DraftAvatarGenerateResponse",
    "DraftAvatarStatusResponse",
    # Identity
    "OnboardingRequest",
    "OnboardingResponse",
    "TopicRequest",
    "TopicResponse",
    "IdentityProfileResponse",
    "UpdateIdentityRequest",
    "IdentityConfidenceResponse",
    "IdentityOnboardingStatusResponse",
    # Channels
    "ChannelConnectRequest",
    "ChannelConnectResponse",
    "ConnectedChannelResponse",
]
