"""
Authentication schemas for request/response validation.

This module provides Pydantic models for:
- User registration and login
- Token requests and responses
- Password management
- Input validation with comprehensive error handling
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import re

from ..models.user import UserRole, UserStatus


class UserRegistrationRequest(BaseModel):
    """Schema for user registration requests."""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Username (3-30 characters, alphanumeric and underscores only)"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters)"
    )
    confirm_password: str = Field(..., description="Password confirmation")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        if v.startswith('_') or v.endswith('_'):
            raise ValueError('Username cannot start or end with underscore')
        if '__' in v:
            raise ValueError('Username cannot contain consecutive underscores')
        return v.lower()  # Store usernames in lowercase
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        # Check for common weak patterns
        weak_patterns = ['password', '12345678', 'qwerty', 'admin']
        if any(pattern in v.lower() for pattern in weak_patterns):
            raise ValueError('Password is too common or weak')
        
        return v
    
    @validator('confirm_password')
    def validate_password_match(cls, v, values):
        """Validate password confirmation matches."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class UserLoginRequest(BaseModel):
    """Schema for user login requests."""
    
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(default=False, description="Extend session duration")
    device_info: Optional[str] = Field(None, max_length=255, description="Device information")


class TokenResponse(BaseModel):
    """Schema for token responses."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    user: "UserResponse" = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh requests."""
    
    refresh_token: str = Field(..., description="Valid refresh token")


class PasswordChangeRequest(BaseModel):
    """Schema for password change requests."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (minimum 8 characters)"
    )
    confirm_new_password: str = Field(..., description="New password confirmation")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v
    
    @validator('confirm_new_password')
    def validate_new_password_match(cls, v, values):
        """Validate new password confirmation matches."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v


class PasswordResetRequest(BaseModel):
    """Schema for password reset requests."""
    
    email: EmailStr = Field(..., description="Registered email address")


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (minimum 8 characters)"
    )
    confirm_new_password: str = Field(..., description="New password confirmation")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        return v
    
    @validator('confirm_new_password')
    def validate_new_password_match(cls, v, values):
        """Validate new password confirmation matches."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('New passwords do not match')
        return v


class UserResponse(BaseModel):
    """Schema for user responses (public user data)."""
    
    id: UUID = Field(..., description="User unique identifier")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    role: UserRole = Field(..., description="User role")
    status: UserStatus = Field(..., description="Account status")
    is_verified: bool = Field(..., description="Email verification status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    max_characters: int = Field(..., description="Maximum characters allowed")
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Schema for user profile updates."""
    
    email: Optional[EmailStr] = Field(None, description="New email address")
    chat_settings: Optional[Dict[str, Any]] = Field(None, description="Chat preferences")
    privacy_settings: Optional[Dict[str, Any]] = Field(None, description="Privacy preferences")


class SessionInfo(BaseModel):
    """Schema for user session information."""
    
    id: UUID = Field(..., description="Session unique identifier")
    device_info: Optional[str] = Field(None, description="Device information")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    is_active: bool = Field(..., description="Session active status")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    
    class Config:
        from_attributes = True


class AuthErrorResponse(BaseModel):
    """Schema for authentication error responses."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class RateLimitResponse(BaseModel):
    """Schema for rate limit information."""
    
    limit: int = Field(..., description="Rate limit (requests per window)")
    remaining: int = Field(..., description="Remaining requests in current window")
    reset: int = Field(..., description="Time when rate limit resets (Unix timestamp)")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retrying")


# Update forward references
TokenResponse.model_rebuild()