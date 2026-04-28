"""
IdentityProfile model — vector embeddings for identity
"""

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.models.base import BaseModel


class IdentityProfile(BaseModel):
    """Stores identity profile with vector embeddings"""
    __tablename__ = "identity_profiles"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Text descriptions
    vocabulary_description = Column(Text, nullable=True)
    communication_style = Column(Text, nullable=True)
    
    # Vector embeddings (1536 dimensions for OpenAI embeddings)
    topics_known_embedding = Column(Vector(1536), nullable=True)
    topics_avoided_embedding = Column(Vector(1536), nullable=True)
    
    # Metadata
    embedding_model = Column(String, default="text-embedding-3-small", nullable=False)
    topics_known_text = Column(Text, nullable=True)  # Raw text for regeneration
    topics_avoided_text = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="identity_profile")
