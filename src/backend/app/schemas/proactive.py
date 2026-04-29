"""Schemas for proactive twin APIs."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field


class ProactiveSuggestionResponse(BaseModel):
    id: str
    suggestion_type: str
    contact_id: Optional[str]
    signal_summary: str
    draft_message: str
    urgency_score: float
    value_score: float
    status: str
    snoozed_until: Optional[datetime] = None
    acted_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProactiveSuggestionListResponse(BaseModel):
    total: int
    items: list[ProactiveSuggestionResponse]


class SuggestionActRequest(BaseModel):
    action: Literal["approve", "dismiss", "never", "snooze"]
    edited_message: Optional[str] = None
    snooze_days: int = Field(default=30, ge=1, le=365)


class ProactivePreferenceResponse(BaseModel):
    enabled: bool
    enabled_types: list[str]
    cold_threshold_days: int
    open_thread_hours: int
    max_suggestions_per_day: int


class ProactivePreferenceUpdateRequest(BaseModel):
    enabled: Optional[bool] = None
    enabled_types: Optional[list[str]] = None
    cold_threshold_days: Optional[int] = Field(default=None, ge=1, le=365)
    open_thread_hours: Optional[int] = Field(default=None, ge=1, le=720)
    max_suggestions_per_day: Optional[int] = Field(default=None, ge=1, le=50)


class ProactiveScanResponse(BaseModel):
    created: int
