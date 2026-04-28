"""
Authentication service
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models import User, Twin, IdentityProfile, AuditLog
from app.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.schemas.auth import SignupRequest, LoginRequest
from datetime import timedelta


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def signup(db: Session, signup_data: SignupRequest) -> User:
        """
        Create a new user account
        
        Raises:
            ValueError: If email already exists
        """
        # Check if user exists
        existing_user = db.query(User).filter(User.email == signup_data.email).first()
        if existing_user:
            raise ValueError(f"Email {signup_data.email} already registered")
        
        # Create user
        user = User(
            email=signup_data.email,
            name=signup_data.name,
            password_hash=hash_password(signup_data.password),
            is_active=True,
        )
        
        db.add(user)
        db.flush()  # Flush to get user ID
        
        # Create empty twin profile
        twin = Twin(user_id=user.id)
        db.add(twin)
        
        # Create empty identity profile
        identity = IdentityProfile(user_id=user.id)
        db.add(identity)
        
        # Log signup action
        audit_log = AuditLog(
            user_id=user.id,
            action="signup",
            resource_type="User",
            resource_id=user.id,
            details={"email": user.email},
        )
        db.add(audit_log)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def login(db: Session, login_data: LoginRequest) -> User:
        """
        Authenticate a user
        
        Raises:
            ValueError: If credentials invalid
        """
        user = db.query(User).filter(User.email == login_data.email).first()
        
        if not user or not verify_password(login_data.password, user.password_hash):
            raise ValueError("Invalid email or password")
        
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        # Log login action
        audit_log = AuditLog(
            user_id=user.id,
            action="login",
            resource_type="User",
            resource_id=user.id,
            details={},
        )
        db.add(audit_log)
        db.commit()
        
        return user
    
    @staticmethod
    def generate_tokens(user_id: str) -> tuple[str, str, int]:
        """
        Generate access and refresh tokens for a user
        
        Returns:
            (access_token, refresh_token, expires_in_seconds)
        """
        # Access token: 24 hours
        access_token, expires_in = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(hours=24),
        )
        
        # Refresh token: 7 days
        refresh_token = create_refresh_token(
            data={"sub": user_id},
            expires_delta=timedelta(days=7),
        )
        
        return access_token, refresh_token, expires_in
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User:
        """Get a user by ID"""
        return db.query(User).filter(User.id == user_id).first()
