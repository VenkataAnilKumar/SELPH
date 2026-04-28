"""
AuditLog model — immutable action trail for compliance
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, utcnow


class AuditLog(BaseModel):
    """Immutable audit log for all user actions"""
    __tablename__ = "audit_logs"

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False)  # signup, login, create_draft, approve_draft, reject_draft, send_response, etc.
    resource_type = Column(String, nullable=True)  # User, Twin, Draft, Message, ChannelCredential
    resource_id = Column(String, nullable=True)
    
    # Details
    details = Column(JSON, default=dict, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        {'extend_existing': True},  # Allow redefinition
    )
