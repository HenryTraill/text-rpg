"""
Authentication schemas for request and response models.

This module defines Pydantic models for:
- User registration and login requests
- Token responses
- User profile responses
- Authentication-related validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from ..models.user import UserRole, UserStatus


class UserRegistrationRequest(BaseModel):
    """User registration request schema."""

    username: str = Field(
        ..., min_length=3, max_length=30, description="Username (3-30 characters)"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ..., min_length=8, description="Password (minimum 8 characters)"
    )
    password_confirm: str = Field(..., description="Password confirmation")

    @validator("username")
    def validate_username(cls, v):
        if not v.isalnum() and "_" not in v:
            raise ValueError(
                "Username must contain only alphanumeric characters and underscores"
            )
        return v.lower()

    @validator("password_confirm")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    """User login request schema."""

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    remember_me: bool = Field(
        default=False, description="Remember login for extended period"
    )
    device_info: Optional[str] = Field(default=None, description="Device information")

    class Config:
        schema_extra = {
            "example": {
                "username": "player123",  # Can also use email: "player@example.com"
                "password": "SecurePassword123",
                "remember_me": True,
                "device_info": "Mobile App v1.0",
            }
        }


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., description="Valid refresh token")


class UserResponse(BaseModel):
    """User response schema (public user information)."""

    id: UUID
    username: str
    email: str
    role: UserRole
    status: UserStatus
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    max_characters: int

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "player123",
                "email": "player@example.com",
                "role": "player",
                "status": "active",
                "is_verified": True,
                "created_at": "2023-01-01T12:00:00Z",
                "last_login": "2023-01-02T08:30:00Z",
                "max_characters": 5,
            }
        }


class UserProfileResponse(BaseModel):
    """Extended user profile response schema."""

    id: UUID
    username: str
    email: str
    role: UserRole
    status: UserStatus
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    max_characters: int
    chat_settings: Dict[str, Any]
    privacy_settings: Dict[str, Any]

    class Config:
        from_attributes = True


class UserProfileUpdateRequest(BaseModel):
    """User profile update request schema."""

    username: Optional[str] = Field(
        None, min_length=3, max_length=30, description="New username (3-30 characters)"
    )
    email: Optional[EmailStr] = Field(None, description="New email address")
    max_characters: Optional[int] = Field(
        None, ge=1, le=10, description="Maximum number of characters (1-10)"
    )
    chat_settings: Optional[Dict[str, Any]] = Field(
        None, description="Chat preferences"
    )
    privacy_settings: Optional[Dict[str, Any]] = Field(
        None, description="Privacy preferences"
    )

    @validator("username")
    def validate_username(cls, v):
        if v is not None:
            if not v.replace("_", "").isalnum():
                raise ValueError(
                    "Username must contain only alphanumeric characters and underscores"
                )
            return v.lower()
        return v

    class Config:
        schema_extra = {
            "example": {
                "username": "newusername",
                "email": "newemail@example.com",
                "max_characters": 3,
                "chat_settings": {"notifications": True, "sound": False},
                "privacy_settings": {"show_online": True, "allow_messages": True},
            }
        }


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., min_length=8, description="New password (minimum 8 characters)"
    )
    new_password_confirm: str = Field(..., description="New password confirmation")

    @validator("new_password_confirm")
    def passwords_match(cls, v, values):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("New passwords do not match")
        return v

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserSessionResponse(BaseModel):
    """User session response schema."""

    id: UUID
    device_info: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_active: bool
    created_at: datetime
    expires_at: datetime
    last_activity: datetime

    class Config:
        from_attributes = True


class LogoutRequest(BaseModel):
    """Logout request schema."""

    revoke_all_sessions: bool = Field(
        default=False, description="Revoke all user sessions"
    )


class AuthenticationResponse(BaseModel):
    """General authentication response schema."""

    message: str
    success: bool
    user: Optional[UserResponse] = None
    tokens: Optional[TokenResponse] = None

    class Config:
        schema_extra = {
            "example": {
                "message": "Authentication successful",
                "success": True,
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "player123",
                    "email": "player@example.com",
                    "role": "player",
                },
                "tokens": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 900,
                },
            }
        }


class ErrorResponse(BaseModel):
    """Error response schema."""

    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    class Config:
        schema_extra = {
            "example": {
                "message": "Authentication failed",
                "error_code": "INVALID_CREDENTIALS",
                "details": {"field": "username", "reason": "User not found"},
            }
        }
