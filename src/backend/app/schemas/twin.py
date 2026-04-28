"""
Pydantic schemas for Twin endpoints
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class TwinResponse(BaseModel):
    """Twin profile response"""
    id: str
    user_id: str
    domain: str
    tone: str
    vocab: list
    avg_response_length: int
    status: str  # active or paused
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TwinStatsResponse(BaseModel):
    """Twin statistics"""
    twin_id: str
    status: str
    domain: str
    tone: str
    total_messages: int
    pending_drafts: int
    processed_drafts: int


class UpdateTwinRequest(BaseModel):
    """Request to update twin profile"""
    domain: Optional[str] = None
    tone: Optional[str] = None
    vocab: Optional[list] = None
    avg_response_length: Optional[int] = None


class MessageResponse(BaseModel):
    """Message response"""
    id: str
    user_id: str
    channel: str
    sender_id: str
    sender_name: str
    content: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DraftResponse(BaseModel):
    """Draft response"""
    id: str
    message_id: str
    user_id: str
    twin_id: str
    content: str
    edited_content: Optional[str]
    confidence_score: float
    confidence_label: str
    moderation_passed: bool
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DraftApprovalRequest(BaseModel):
    """Request to approve, edit, or reject a draft"""
    action: str  # approve, reject, edit, skip
    edited_content: Optional[str] = None  # Required if action == "edit"


class IdentityProfileResponse(BaseModel):
    """Identity profile response"""
    vocabulary_description: Optional[str]
    communication_style: Optional[str]
    topics_known: list
    topics_avoided: list


class UpdateIdentityRequest(BaseModel):
    """Request to update identity profile"""
    vocabulary_description: Optional[str] = None
    communication_style: Optional[str] = None
    topics_known: Optional[list] = None
    topics_avoided: Optional[list] = None
