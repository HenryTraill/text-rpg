"""
<<<<<<< Updated upstream
Authentication utilities for JWT token handling and password management.

This module provides:
- JWT token creation and validation
- Password hashing and verification
- Token refresh mechanism
- User authentication functions
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
from sqlmodel import Session, select

from .config import settings
from ..models.user import User, UserSession
=======
Authentication and JWT token utilities for the text RPG backend.

Provides JWT token creation, validation, and user authentication functionality.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext

from .config import settings
>>>>>>> Stashed changes

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

<<<<<<< Updated upstream
# HTTP Bearer token handler
security = HTTPBearer()


class AuthUtils:
    """Authentication utility class for JWT and password operations."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "jti": str(uuid4()),  # JWT ID for token revocation
            }
        )

        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=7)

        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "jti": str(uuid4()),
                "type": "refresh",
            }
        )

        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.algorithm
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

    @staticmethod
    async def get_user_by_username(session: Session, username: str) -> Optional[User]:
        """Get user by username (case-insensitive)."""
        statement = select(User).where(User.username.ilike(username))
        result = await session.execute(statement)
        return result.scalars().first()

    @staticmethod
    async def get_user_by_email(session: Session, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)."""
        statement = select(User).where(User.email.ilike(email))
        result = await session.execute(statement)
        return result.scalars().first()

    @staticmethod
    async def get_user_by_id(session: Session, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        statement = select(User).where(User.id == user_id)
        result = await session.execute(statement)
        return result.scalars().first()

    @staticmethod
    async def authenticate_user(
        session: Session, username: str, password: str
    ) -> Optional[User]:
        """Authenticate user with username/email and password."""
        # Try to find user by username first
        user = await AuthUtils.get_user_by_username(session, username)

        # If not found, try by email (case-insensitive)
        if not user:
            user = await AuthUtils.get_user_by_email(session, username)

        if not user:
            return None
        if not AuthUtils.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    async def create_user_session(
        session: Session,
        user_id: UUID,
        token_jti: str,
        expires_at: datetime,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> UserSession:
        """Create a new user session record."""
        user_session = UserSession(
            user_id=user_id,
            token_jti=token_jti,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        session.add(user_session)
        await session.commit()
        await session.refresh(user_session)
        return user_session

    @staticmethod
    async def revoke_user_session(session: Session, token_jti: str) -> bool:
        """Revoke a user session by token JTI."""
        statement = select(UserSession).where(UserSession.token_jti == token_jti)
        result = await session.execute(statement)
        user_session = result.scalars().first()

        if user_session:
            user_session.is_active = False
            session.add(user_session)
            await session.commit()
            return True
        return False

    @staticmethod
    async def is_token_revoked(session: Session, token_jti: str) -> bool:
        """Check if a token is revoked."""
        statement = select(UserSession).where(
            UserSession.token_jti == token_jti, UserSession.is_active
        )
        result = await session.execute(statement)
        return result.scalars().first() is None


# Global auth utilities instance
auth_utils = AuthUtils()
=======

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        InvalidTokenError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise JWTError("Invalid or expired token")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Data to encode in the token
        
    Returns:
        JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # Refresh tokens last 7 days
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt 
>>>>>>> Stashed changes
