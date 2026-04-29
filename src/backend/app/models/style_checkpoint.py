"""Style evolution checkpoints for profile refresh decisions."""

from sqlalchemy import Column, String, Float, JSON, Text, DateTime, ForeignKey, Index
from app.models.base import BaseModel


class StyleCheckpoint(BaseModel):
    __tablename__ = "style_checkpoints"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(String, ForeignKey("identity_variants.id"), nullable=True)
    trigger_type = Column(String(50), nullable=False)
    divergence_score = Column(Float, nullable=False)
    delta_report = Column(JSON, nullable=False, default=dict)
    sample_old = Column(Text, nullable=False)
    sample_new = Column(Text, nullable=False)
    decision = Column(String(50), nullable=True)
    updated_dimensions = Column(JSON, nullable=True)
    decided_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_style_checkpoints_user_decision", "user_id", "decision"),
    )
