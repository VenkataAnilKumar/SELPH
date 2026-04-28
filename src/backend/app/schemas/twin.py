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
    total_estimated_tokens: int
    total_estimated_cost_usd: float
    fallback_rate: float
    approval_rate: float  # approved+edited / (approved+edited+rejected) — primary Phase 3 metric
    generation_source_breakdown: dict[str, int]
    model_breakdown: dict[str, int]
    fallback_reason_breakdown: dict[str, int]

    model_config = ConfigDict(protected_namespaces=())


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
    generation_source: Optional[str]
    llm_model: Optional[str]
    fallback_reason: Optional[str]
    llm_calls: Optional[int]
    parse_retry_count: Optional[int]
    llm_latency_ms: Optional[int]
    pipeline_latency_ms: Optional[int]
    estimated_input_tokens: Optional[int]
    estimated_output_tokens: Optional[int]
    estimated_total_tokens: Optional[int]
    estimated_cost_usd: Optional[float]
    voice_status: Optional[str]
    voice_audio_url: Optional[str]
    voice_provider: Optional[str]
    voice_model_id: Optional[str]
    voice_error: Optional[str]
    avatar_status: Optional[str]
    avatar_video_url: Optional[str]
    avatar_provider: Optional[str]
    avatar_model_id: Optional[str]
    avatar_error: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DraftApprovalRequest(BaseModel):
    """Request to approve, edit, or reject a draft"""
    action: str  # approve, reject, edit, skip
    edited_content: Optional[str] = None  # Required if action == "edit"


class DraftVoiceGenerateRequest(BaseModel):
    """Request payload to queue voice synthesis for a draft."""

    voice_model_id: Optional[str] = None


class DraftVoiceGenerateResponse(BaseModel):
    """Queue response for draft voice synthesis."""

    draft_id: str
    queued: bool
    voice_status: str
    task_id: Optional[str] = None


class DraftVoiceStatusResponse(BaseModel):
    """Voice synthesis status for a draft."""

    draft_id: str
    voice_status: str
    voice_audio_url: Optional[str] = None
    voice_provider: Optional[str] = None
    voice_model_id: Optional[str] = None
    voice_error: Optional[str] = None


class DraftAvatarGenerateRequest(BaseModel):
    """Request payload to queue avatar generation for a draft."""

    avatar_model_id: Optional[str] = None
    voice_audio_url: Optional[str] = None


class DraftAvatarGenerateResponse(BaseModel):
    """Queue response for draft avatar generation."""

    draft_id: str
    queued: bool
    avatar_status: str
    task_id: Optional[str] = None


class DraftAvatarStatusResponse(BaseModel):
    """Avatar generation status for a draft."""

    draft_id: str
    avatar_status: str
    avatar_video_url: Optional[str] = None
    avatar_provider: Optional[str] = None
    avatar_model_id: Optional[str] = None
    avatar_error: Optional[str] = None



