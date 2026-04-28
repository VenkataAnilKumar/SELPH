"""
Base model with common fields
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()


class BaseModel(Base):
    """Abstract base class for all models"""
    __abstract__ = True

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
