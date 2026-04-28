"""
Topic model — known and avoided topics for twin
"""

from sqlalchemy import Column, String, Text, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.models.base import BaseModel


class Topic(BaseModel):
    """Known or avoided topics for the twin"""
    __tablename__ = "topics"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String, nullable=False)  # e.g., "mental health", "investment advice"
    topic_type = Column(String, nullable=False)  # "known" or "avoided"
    context = Column(Text, nullable=True)  # Description/context
    
    # Vector for semantic search
    embedding = Column(Vector(1536), nullable=True)
    
    # Usage tracking
    frequency = Column(Integer, default=1, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="topics")

    __table_args__ = (
        Index("ix_topics_user_id_type", "user_id", "topic_type"),
    )
