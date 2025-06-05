from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID, uuid4
import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    PLAYER = "player"
    MODERATOR = "moderator"
    ADMIN = "admin"
    DEVELOPER = "developer"


class UserStatus(str, enum.Enum):
    """User account status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    PENDING_VERIFICATION = "pending_verification"


class User(SQLModel, table=True):
    """
    User model for authentication and account management.
    
    This represents a player's account that can have multiple characters.
    """
    __tablename__ = "users"
    
    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Authentication fields
    username: str = Field(index=True, unique=True, min_length=3, max_length=30)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    
    # Account status
    role: UserRole = Field(default=UserRole.PLAYER)
    status: UserStatus = Field(default=UserStatus.PENDING_VERIFICATION)
    is_verified: bool = Field(default=False)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = Field(default=None)
    
    # Account limits and preferences
    max_characters: int = Field(default=5)
    chat_settings: Optional[dict] = Field(default_factory=dict, sa_column_kwargs={"type_": "JSON"})
    privacy_settings: Optional[dict] = Field(default_factory=dict, sa_column_kwargs={"type_": "JSON"})
    
    # Login tracking
    login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = Field(default=None)
    
    # Relationships
    characters: List["Character"] = Relationship(back_populates="user")
    sessions: List["UserSession"] = Relationship(back_populates="user")


class UserSession(SQLModel, table=True):
    """
    User session model for JWT token tracking and management.
    
    Tracks active user sessions for security and session management.
    """
    __tablename__ = "user_sessions"
    
    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    
    # Foreign Keys
    user_id: UUID = Field(foreign_key="users.id", index=True)
    
    # Session data
    token_jti: str = Field(index=True, unique=True)  # JWT ID for token revocation
    device_info: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    
    # Session status
    is_active: bool = Field(default=True)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user: User = Relationship(back_populates="sessions")