"""Schemas for privacy processing mode APIs."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class PrivacySettingsResponse(BaseModel):
    processing_mode: str
    on_device_capable: bool
    voice_clone_enabled: bool
    avatar_enabled: bool
    cloud_sync_scope: str


class PrivacySettingsUpdateRequest(BaseModel):
    processing_mode: Optional[Literal["cloud", "hybrid", "on_device"]] = None
    cloud_sync_scope: Optional[Literal["full", "metadata_only", "none"]] = None
    voice_clone_enabled: Optional[bool] = None
    avatar_enabled: Optional[bool] = None


class PrivacyCapabilityRequest(BaseModel):
    on_device_capable: bool


class PrivacyCapabilityResponse(BaseModel):
    updated: bool


class AccountDeletionRequest(BaseModel):
    """Explicit, re-authenticated request to erase the account and all data."""

    password: str
    confirm: str  # must be exactly "DELETE MY ACCOUNT"


class DeletionCertificateResponse(BaseModel):
    certificate_id: str
    subject_hash: str
    completed_at: datetime
    summary: dict
    signature: str
    valid: bool = True
