"""
Pydantic schemas for authentication
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignupRequest(BaseModel):
    """Request body for user signup"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "name": "John Doe",
            }
        }


class LoginRequest(BaseModel):
    """Request body for user login"""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
            }
        }


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds


class UserResponse(BaseModel):
    """User object response"""
    id: str
    email: str
    name: str
    is_active: bool

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Complete auth response with user and tokens"""
    user: UserResponse
    tokens: TokenResponse
