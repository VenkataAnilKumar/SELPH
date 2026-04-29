"""Map channels/accounts to identity variants."""

from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint, Index
from app.models.base import BaseModel


class ChannelProfileMapping(BaseModel):
    __tablename__ = "channel_profile_mappings"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(String, ForeignKey("identity_variants.id"), nullable=False, index=True)
    channel = Column(String(50), nullable=False)
    platform_account = Column(String(200), nullable=True)
    priority = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("user_id", "channel", "platform_account", name="uq_channel_profile_mapping"),
        Index("ix_channel_profile_mappings_user_channel", "user_id", "channel"),
    )
