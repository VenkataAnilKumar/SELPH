"""
Database configuration and session management
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.models import Base

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    # Use NullPool in development for simplicity, change to QueuePool in production
    poolclass=NullPool if settings.environment == "development" else None,
    echo=settings.debug,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Session:
    """
    Dependency: Get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Enable pgvector extension on PostgreSQL
@event.listens_for(engine, "connect")
def enable_pgvector(dbapi_conn, connection_record):
    """Enable pgvector extension on connection"""
    if settings.database_url.startswith("postgresql"):
        cursor = dbapi_conn.cursor()
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            dbapi_conn.commit()
        except Exception:
            dbapi_conn.rollback()
        finally:
            cursor.close()
