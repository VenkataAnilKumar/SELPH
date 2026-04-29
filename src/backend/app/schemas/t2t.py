"""Schemas for twin-to-twin protocol APIs."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


class T2TSessionResponse(BaseModel):
    id: str
    initiating_twin: str
    receiving_twin: str
    session_type: str
    status: str
    negotiation_log: list
    proposal: Optional[dict] = None
    initiator_approved: Optional[bool] = None
    receiver_approved: Optional[bool] = None
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class T2TSessionListResponse(BaseModel):
    total: int
    items: list[T2TSessionResponse]


class T2TApproveRequest(BaseModel):
    twin_id: str
    approved: bool = True


class T2TRejectRequest(BaseModel):
    twin_id: str
    reason: Optional[str] = None


class T2TExitRequest(BaseModel):
    twin_id: str


class T2TCreateRequest(BaseModel):
    receiving_twin: str
    session_type: Literal["scheduling", "availability", "introduction"]
