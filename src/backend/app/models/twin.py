"""
Twin model — the digital twin profile
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Twin(BaseModel):
    """Twin profile with identity data"""
    __tablename__ = "twins"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    domain = Column(String, default="professional", nullable=False)  # e.g., "professional", "personal"
    tone = Column(String, default="friendly", nullable=False)  # e.g., "formal", "casual", "friendly"
    vocab = Column(JSON, default=list, nullable=False)  # List of tone/vocabulary keywords
    avg_response_length = Column(Integer, default=150, nullable=False)  # average words
    status = Column(String, default="active", nullable=False)  # "active" or "paused"
    twin_operating_mode = Column(String, default="normal", nullable=False)  # normal, crisis_alert, crisis_mode, manual_pause
    
    # Relationships
    user = relationship("User", back_populates="twin")
    drafts = relationship("Draft", back_populates="twin", cascade="all, delete-orphan")
