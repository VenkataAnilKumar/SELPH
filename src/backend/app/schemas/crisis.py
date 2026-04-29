"""Schemas for crisis and surge APIs."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field


class SurgeStatusResponse(BaseModel):
    mode: str
    has_active_event: bool
    trigger_type: Optional[str] = None
    peak_rate: Optional[float] = None
    baseline_rate: Optional[float] = None


class CrisisActivateRequest(BaseModel):
    mode: Literal["crisis_alert", "crisis_mode", "manual_pause"] = "crisis_mode"
    trigger_type: str = "manual"


class CrisisResolveRequest(BaseModel):
    resolution_type: str = "manual_resume"


class CrisisTemplateCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    template_type: Literal["acknowledge", "clarify", "appreciation", "custom"] = "custom"


class CrisisTemplateResponse(BaseModel):
    id: str
    label: str
    content: str
    template_type: str
    approved_at: datetime
    last_used_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CrisisTemplateListResponse(BaseModel):
    total: int
    items: list[CrisisTemplateResponse]
