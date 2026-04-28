"""
Draft model — drafted responses awaiting approval
"""

from sqlalchemy import Column, String, Text, ForeignKey, Float, Boolean, JSON, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Draft(BaseModel):
    """Draft response awaiting user approval"""
    __tablename__ = "drafts"

    message_id = Column(String, ForeignKey("messages.id"), nullable=False, unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    twin_id = Column(String, ForeignKey("twins.id"), nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    edited_content = Column(Text, nullable=True)
    sent_response = Column(Text, nullable=True)
    
    # Confidence scoring
    confidence_score = Column(Float, default=0.5, nullable=False)  # 0.0 - 1.0
    confidence_label = Column(String, default="Medium", nullable=False)  # High, Medium, Low
    confidence_reasoning = Column(Text, nullable=True)
    
    # Safety
    moderation_passed = Column(Boolean, default=False, nullable=False)
    moderation_flags = Column(JSON, default=list, nullable=False)  # List of flags if any
    
    # Status
    status = Column(String, default="pending_approval", nullable=False)  # pending_approval, approved, edited, rejected, sent
    user_action = Column(String, nullable=True)  # approve, edit, reject, skip
    
    # Relationships
    message = relationship("Message", back_populates="draft")
    user = relationship("User", back_populates="drafts")
    twin = relationship("Twin", back_populates="drafts")

    __table_args__ = (
        Index("ix_drafts_user_id_status", "user_id", "status"),
        Index("ix_drafts_twin_id", "twin_id"),
    )
