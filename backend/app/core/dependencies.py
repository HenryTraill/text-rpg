"""
FastAPI dependencies for authentication and authorization.

This module provides:
- JWT token validation dependencies
- User authentication dependencies
- Role-based access control
- Rate limiting dependencies
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from uuid import UUID

from .database import get_session
from .security import verify_token, TokenData
from .rate_limiting import check_rate_limit, add_rate_limit_headers
from ..models.user import User, UserStatus, UserRole
from ..models.user import UserSession


# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> Optional[User]:
    """
    Get current user from JWT token (optional - returns None if no token).
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer token
        session: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        # Verify token
        token_data = verify_token(credentials.credentials, "access")
        
        # Get user from database
        user = session.get(User, UUID(token_data.user_id))
        if not user:
            return None
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            return None
        
        # Update last activity (optional - could be moved to middleware)
        # This helps track active sessions
        
        return user
        
    except HTTPException:
        return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """
    Get current user from JWT token (required - raises exception if no valid token).
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer token
        session: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    token_data = verify_token(credentials.credentials, "access")
    
    # Get user from database
    user = session.get(User, UUID(token_data.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}",
        )
    
    # Check if user is locked out
    if user.locked_until and user.locked_until.timestamp() > user.created_at.timestamp():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for get_current_user).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Active user object
    """
    return current_user


async def require_role(required_role: UserRole):
    """
    Create a dependency that requires a specific user role.
    
    Args:
        required_role: Required user role
        
    Returns:
        Dependency function
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role.value} role"
            )
        return current_user
    
    return role_checker


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Admin user object
        
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.DEVELOPER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires admin privileges"
        )
    return current_user


async def require_moderator(current_user: User = Depends(get_current_user)) -> User:
    """
    Require moderator role or higher.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Moderator/admin user object
        
    Raises:
        HTTPException: If user is not moderator or admin
    """
    if current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN, UserRole.DEVELOPER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires moderator privileges or higher"
        )
    return current_user


async def apply_rate_limit(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    limit: int = 100,
    window: int = 60
) -> dict:
    """
    Apply rate limiting to the current request.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user (optional)
        limit: Rate limit (requests per window)
        window: Time window in seconds
        
    Returns:
        Rate limit information
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    user_id = str(current_user.id) if current_user else None
    return await check_rate_limit(
        request=request,
        user_id=user_id,
        limit=limit,
        window=window
    )


async def verify_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> tuple[User, str]:
    """
    Verify refresh token and return user and JTI.
    
    Args:
        credentials: HTTP Bearer token (should be refresh token)
        session: Database session
        
    Returns:
        Tuple of (User object, JWT ID)
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify refresh token
    token_data = verify_token(credentials.credentials, "refresh")
    
    # Get user from database
    user = session.get(User, UUID(token_data.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}",
        )
    
    # Check if the refresh token session exists and is active
    statement = select(UserSession).where(
        UserSession.user_id == user.id,
        UserSession.token_jti == token_data.jti,
        UserSession.is_active == True
    )
    session_result = session.exec(statement).first()
    
    if not session_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user, token_data.jti