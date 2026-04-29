"""Schemas for style evolution APIs."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


class StyleCheckpointResponse(BaseModel):
    id: str
    trigger_type: str
    divergence_score: float
    delta_report: dict
    sample_old: str
    sample_new: str
    decision: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StyleCheckpointListResponse(BaseModel):
    total: int
    items: list[StyleCheckpointResponse]


class StyleDecisionRequest(BaseModel):
    decision: Literal["update", "keep", "partial"]
    updated_dimensions: Optional[dict] = None


class StyleRefreshResponse(BaseModel):
    checkpoint_id: str
    divergence_score: float
