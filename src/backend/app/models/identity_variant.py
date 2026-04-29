"""Multi-identity profile variants for one user."""

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Index
from app.models.base import BaseModel


class IdentityVariant(BaseModel):
    __tablename__ = "identity_variants"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    profile_name = Column(String(100), nullable=False)
    profile_type = Column(String(50), nullable=False, default="personal_brand")
    is_primary = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    vocabulary_description = Column(Text, nullable=True)
    communication_style = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_identity_variants_user_active", "user_id", "is_active"),
    )
