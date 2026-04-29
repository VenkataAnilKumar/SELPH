"""Pre-approved templates used during crisis mode."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from app.models.base import BaseModel


class CrisisTemplate(BaseModel):
    __tablename__ = "crisis_templates"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    label = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    template_type = Column(String(50), nullable=False)
    approved_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
