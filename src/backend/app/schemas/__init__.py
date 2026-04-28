"""
Pydantic schemas for API requests/responses
"""

from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    AuthResponse,
)

from app.schemas.twin import (
    TwinResponse,
    TwinStatsResponse,
    UpdateTwinRequest,
    MessageResponse,
    DraftResponse,
    DraftApprovalRequest,
    IdentityProfileResponse,
    UpdateIdentityRequest,
)

__all__ = [
    # Auth
    "SignupRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "AuthResponse",
    # Twin & Identity
    "TwinResponse",
    "TwinStatsResponse",
    "UpdateTwinRequest",
    "IdentityProfileResponse",
    "UpdateIdentityRequest",
    # Messages & Drafts
    "MessageResponse",
    "DraftResponse",
    "DraftApprovalRequest",
]
