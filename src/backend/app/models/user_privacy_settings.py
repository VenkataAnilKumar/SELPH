"""Per-user privacy and processing mode settings."""

from sqlalchemy import Column, String, Boolean, ForeignKey
from app.models.base import BaseModel


class UserPrivacySettings(BaseModel):
    __tablename__ = "user_privacy_settings"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    processing_mode = Column(String(20), nullable=False, default="cloud")
    on_device_capable = Column(Boolean, nullable=False, default=False)
    voice_clone_enabled = Column(Boolean, nullable=False, default=True)
    avatar_enabled = Column(Boolean, nullable=False, default=True)
    cloud_sync_scope = Column(String(50), nullable=False, default="full")
