"""
Batch send model for message cluster personalization queue.
"""

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Index
from app.models.base import BaseModel


class BatchSend(BaseModel):
    """Queued personalized send item generated from an approved batch template."""

    __tablename__ = "batch_sends"

    cluster_id = Column(String, ForeignKey("message_clusters.id"), nullable=False, index=True)
    message_id = Column(String, ForeignKey("messages.id"), nullable=False, index=True)
    draft_id = Column(String, ForeignKey("drafts.id"), nullable=True, index=True)
    sender_id = Column(String(200), nullable=False)
    personalized_text = Column(Text, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="queued")  # queued, sent, failed

    __table_args__ = (
        Index("ix_batch_sends_cluster_status", "cluster_id", "status"),
    )
