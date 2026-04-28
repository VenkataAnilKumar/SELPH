"""
Base model with common fields
"""

from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()


def utcnow() -> datetime:
    """Return a UTC timestamp without using deprecated utcnow()."""
    return datetime.now(UTC).replace(tzinfo=None)


class BaseModel(Base):
    """Abstract base class for all models"""
    __abstract__ = True

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
