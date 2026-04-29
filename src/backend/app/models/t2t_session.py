"""Twin-to-twin session state and negotiation log."""

from sqlalchemy import Column, String, DateTime, JSON, Boolean, Index
from app.models.base import BaseModel


class T2TSession(BaseModel):
    __tablename__ = "t2t_sessions"

    initiating_twin = Column(String(50), nullable=False)
    receiving_twin = Column(String(50), nullable=False)
    session_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="handshake")
    negotiation_log = Column(JSON, nullable=False, default=list)
    proposal = Column(JSON, nullable=True)
    initiator_approved = Column(Boolean, nullable=True)
    receiver_approved = Column(Boolean, nullable=True)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("ix_t2t_sessions_status", "status"),
    )
