"""
Batch message cluster model for Phase 9 Batch Pattern Approval foundation.
"""

from sqlalchemy import Column, String, Text, ForeignKey, Integer, DateTime, JSON, Index
from app.models.base import BaseModel


class MessageCluster(BaseModel):
    """Cluster of semantically similar messages requiring one template approval."""

    __tablename__ = "message_clusters"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    cluster_label = Column(String(200), nullable=False)
    cluster_summary = Column(Text, nullable=False)
    message_ids = Column(JSON, nullable=False, default=list)
    message_count = Column(Integer, nullable=False, default=0)
    template_draft = Column(Text, nullable=False)
    template_approved = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, rejected, sent
    approved_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_message_clusters_user_status", "user_id", "status"),
    )
