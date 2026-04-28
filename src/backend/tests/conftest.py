"""
Backend test configuration and fixtures
"""

import pytest
import asyncio
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.models.user import User
from app.models.twin import Twin
from app.models.identity_profile import IdentityProfile


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test"""
    # Use in-memory SQLite for tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Override dependency
    app.dependency_overrides[get_db] = override_get_db
    
    db = TestingSessionLocal()
    yield db
    db.close()
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client"""
    return TestClient(app)


@pytest.fixture(scope="function")
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
    }


@pytest.fixture(scope="function")
def test_user(test_db, test_user_data):
    """Create a test user"""
    from app.services.auth import AuthService
    
    service = AuthService()
    user = service.signup(test_db, test_user_data["email"], test_user_data["password"])
    return user


@pytest.fixture(scope="function")
def auth_headers(client, test_user_data):
    """Get auth headers for test user"""
    # Signup
    client.post("/v1/auth/signup", json=test_user_data)
    
    # Login
    response = client.post("/v1/auth/login", json=test_user_data)
    data = response.json()
    
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture(scope="function")
def test_message_data():
    """Test message data"""
    return {
        "channel": "instagram_dm",
        "sender_id": "user_123",
        "sender_name": "John Doe",
        "content": "Hey, how are you?",
        "channel_metadata": {"conversation_id": "conv_123"},
    }


@pytest.fixture(scope="function")
def test_twin_data():
    """Test twin settings data"""
    return {
        "domain": "business",
        "tone": "professional",
        "vocab": "formal",
        "avg_response_length": "medium",
    }
