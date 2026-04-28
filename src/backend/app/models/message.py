"""
Message model — incoming messages from channels
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Message(BaseModel):
    """Incoming message from a channel"""
    __tablename__ = "messages"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    channel = Column(String, nullable=False)  # instagram_dm, gmail, twitter_dm, whatsapp, slack
    sender_id = Column(String, nullable=False)  # External ID from channel (Instagram user ID, etc.)
    sender_name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String, default="received", nullable=False)  # received, processed, draft_ready
    channel_metadata = Column(JSON, default=dict, nullable=False)  # Channel-specific data (msg ID, timestamp, etc.)
    
    # Relationships
    user = relationship("User", back_populates="messages")
    draft = relationship("Draft", back_populates="message", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_messages_user_id_channel", "user_id", "channel"),
        Index("ix_messages_status", "status"),
    )
