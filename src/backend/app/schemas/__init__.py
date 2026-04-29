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
    TwinPerformanceSummaryResponse,
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
    BatchClusterCreateRequest,
    BatchClusterResponse,
    BatchClusterListResponse,
    BatchTemplateApprovalRequest,
    BatchSendResponse,
    BatchSendListResponse,
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
from app.schemas.proactive import (
    ProactiveSuggestionResponse,
    ProactiveSuggestionListResponse,
    SuggestionActRequest,
    ProactivePreferenceResponse,
    ProactivePreferenceUpdateRequest,
)
from app.schemas.crisis import (
    SurgeStatusResponse,
    CrisisActivateRequest,
    CrisisResolveRequest,
    CrisisTemplateCreateRequest,
    CrisisTemplateResponse,
    CrisisTemplateListResponse,
)
from app.schemas.style import (
    StyleCheckpointResponse,
    StyleCheckpointListResponse,
    StyleDecisionRequest,
)
from app.schemas.verification import (
    CertificateResponse,
    VerificationResultResponse,
    CertificateMetadataResponse,
)
from app.schemas.privacy import (
    PrivacySettingsResponse,
    PrivacySettingsUpdateRequest,
    PrivacyCapabilityRequest,
    PrivacyCapabilityResponse,
)
from app.schemas.t2t import (
    T2TSessionResponse,
    T2TSessionListResponse,
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
    "TwinPerformanceSummaryResponse",
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
    "BatchClusterCreateRequest",
    "BatchClusterResponse",
    "BatchClusterListResponse",
    "BatchTemplateApprovalRequest",
    "BatchSendResponse",
    "BatchSendListResponse",
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
    # Proactive
    "ProactiveSuggestionResponse",
    "ProactiveSuggestionListResponse",
    "SuggestionActRequest",
    "ProactivePreferenceResponse",
    "ProactivePreferenceUpdateRequest",
    # Crisis
    "SurgeStatusResponse",
    "CrisisActivateRequest",
    "CrisisResolveRequest",
    "CrisisTemplateCreateRequest",
    "CrisisTemplateResponse",
    "CrisisTemplateListResponse",
    # Style
    "StyleCheckpointResponse",
    "StyleCheckpointListResponse",
    "StyleDecisionRequest",
    # Verification
    "CertificateResponse",
    "VerificationResultResponse",
    "CertificateMetadataResponse",
    # Privacy
    "PrivacySettingsResponse",
    "PrivacySettingsUpdateRequest",
    "PrivacyCapabilityRequest",
    "PrivacyCapabilityResponse",
    # T2T
    "T2TSessionResponse",
    "T2TSessionListResponse",
]
