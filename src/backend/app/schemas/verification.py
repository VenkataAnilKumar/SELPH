"""Schemas for twin verification APIs."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
    twin_public_id: str
    public_key: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None


class VerificationResultResponse(BaseModel):
    twin_id: str
    message_hash: str
    valid: bool
    reason: Optional[str] = None


class CertificateMetadataResponse(BaseModel):
    twin_public_id: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime] = None


class CertificateRevokeRequest(BaseModel):
    reason: Optional[str] = None
