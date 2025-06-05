"""
Security utilities for authentication and authorization.

This module provides:
- JWT token creation and validation
- Password hashing and verification
- Token refresh mechanisms
- Security dependencies for FastAPI
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import uuid4
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import BaseModel

from .config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token data model for JWT validation"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    jti: Optional[str] = None
    token_type: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def create_password_hash(password: str) -> str:
    """
    Create a bcrypt hash of the password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (default: 15 minutes)
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4()),  # JWT ID for token revocation
        "token_type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (default: 7 days)
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4()),  # JWT ID for token revocation
        "token_type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        TokenData object with decoded claims
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # Verify token type
        if payload.get("token_type") != token_type:
            raise credentials_exception
        
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        jti: str = payload.get("jti")
        
        if username is None or user_id is None or jti is None:
            raise credentials_exception
            
        token_data = TokenData(
            username=username, 
            user_id=user_id, 
            jti=jti, 
            token_type=token_type
        )
        return token_data
        
    except jwt.PyJWTError:
        raise credentials_exception


def create_token_pair(user_id: str, username: str) -> TokenResponse:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: User UUID
        username: Username
        
    Returns:
        TokenResponse with both tokens
    """
    # Create access token (15 minutes)
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        data={"sub": username, "user_id": str(user_id)},
        expires_delta=access_token_expires
    )
    
    # Create refresh token (7 days)
    refresh_token_expires = timedelta(days=7)
    refresh_token = create_refresh_token(
        data={"sub": username, "user_id": str(user_id)},
        expires_delta=refresh_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_token_expires.total_seconds())
    )