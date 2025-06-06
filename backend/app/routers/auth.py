"""
Authentication router for user registration, login, and session management.

This module provides:
- User registration and login endpoints
- JWT token generation and refresh
- Session management and logout
- Password change functionality
- User profile management
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
import logging

from ..core.database import get_session
from ..core.auth import auth_utils
from ..models.user import User, UserSession, UserStatus
from ..schemas.auth import (
    UserRegistrationRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    UserProfileResponse,
    PasswordChangeRequest,
    UserSessionResponse,
    LogoutRequest,
    AuthenticationResponse,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])


# Dependency to get current user from token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: JWT token from Authorization header
        session: Database session

    Returns:
        Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Verify token
        payload = auth_utils.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        token_jti = payload.get("jti")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        # Check if token is revoked
        if await auth_utils.is_token_revoked(session, token_jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

        # Get user from database
        user = await auth_utils.get_user_by_id(session, UUID(user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        # Check user status
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active",
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )


# Optional dependency for current user (doesn't raise if not authenticated)
async def get_current_user_optional(
    request: Request, session: Session = Depends(get_session)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=auth_header.split(" ")[1]
        )

        return await get_current_user(credentials, session)
    except Exception:
        return None


@router.post("/register", response_model=AuthenticationResponse)
async def register_user(
    user_data: UserRegistrationRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Register a new user account.

    Args:
        user_data: User registration data
        request: HTTP request for metadata
        session: Database session

    Returns:
        Authentication response with user and tokens
    """
    try:
        # Check if username already exists
        existing_user = await auth_utils.get_user_by_username(
            session, user_data.username
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        # Check if email already exists
        existing_email = await auth_utils.get_user_by_email(session, user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user
        hashed_password = auth_utils.get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            status=UserStatus.ACTIVE,  # Auto-activate for now
            is_verified=True,  # Auto-verify for now
        )

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        # Generate tokens
        access_token_expires = timedelta(minutes=15)
        refresh_token_expires = timedelta(days=7)

        access_token = auth_utils.create_access_token(
            data={"sub": str(new_user.id)}, expires_delta=access_token_expires
        )

        refresh_token = auth_utils.create_refresh_token(
            data={"sub": str(new_user.id)}, expires_delta=refresh_token_expires
        )

        # Create user session
        access_payload = auth_utils.verify_token(access_token)
        await auth_utils.create_user_session(
            session=session,
            user_id=new_user.id,
            token_jti=access_payload["jti"],
            expires_at=datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Update last login
        new_user.last_login = datetime.now()
        session.add(new_user)
        session.commit()

        logger.info(f"New user registered: {new_user.username}")

        return AuthenticationResponse(
            message="Registration successful",
            success=True,
            user=UserResponse.from_orm(new_user),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=int(access_token_expires.total_seconds()),
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=AuthenticationResponse)
async def login_user(
    login_data: UserLoginRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Authenticate user and return tokens.

    Args:
        login_data: User login credentials
        request: HTTP request for metadata
        session: Database session

    Returns:
        Authentication response with user and tokens
    """
    try:
        # Authenticate user
        user = await auth_utils.authenticate_user(
            session, login_data.username, login_data.password
        )

        if not user:
            # Log failed login attempt
            logger.warning(f"Failed login attempt for: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        # Check user status
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is not active"
            )

        # Generate tokens
        access_token_expires = timedelta(minutes=15)
        refresh_token_expires = timedelta(days=7 if login_data.remember_me else 1)

        access_token = auth_utils.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        refresh_token = auth_utils.create_refresh_token(
            data={"sub": str(user.id)}, expires_delta=refresh_token_expires
        )

        # Create user session
        access_payload = auth_utils.verify_token(access_token)
        await auth_utils.create_user_session(
            session=session,
            user_id=user.id,
            token_jti=access_payload["jti"],
            expires_at=datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc),
            device_info=login_data.device_info,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Update last login
        user.last_login = datetime.now()
        user.login_attempts = 0  # Reset failed attempts
        session.add(user)
        session.commit()

        logger.info(f"User logged in: {user.username}")

        return AuthenticationResponse(
            message="Login successful",
            success=True,
            user=UserResponse.from_orm(user),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=int(access_token_expires.total_seconds()),
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token data
        request: HTTP request for metadata
        session: Database session

    Returns:
        New token pair
    """
    try:
        # Verify refresh token
        payload = auth_utils.verify_token(refresh_data.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        # Get user
        user = await auth_utils.get_user_by_id(session, UUID(user_id))
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Generate new tokens
        access_token_expires = timedelta(minutes=15)
        refresh_token_expires = timedelta(days=7)

        new_access_token = auth_utils.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )

        new_refresh_token = auth_utils.create_refresh_token(
            data={"sub": str(user.id)}, expires_delta=refresh_token_expires
        )

        # Create new session
        access_payload = auth_utils.verify_token(new_access_token)
        await auth_utils.create_user_session(
            session=session,
            user_id=user.id,
            token_jti=access_payload["jti"],
            expires_at=datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        logger.info(f"Token refreshed for user: {user.username}")

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=int(access_token_expires.total_seconds()),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed"
        )


@router.post("/logout")
async def logout_user(
    logout_data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
):
    """
    Logout user and revoke tokens.

    Args:
        logout_data: Logout options
        current_user: Current authenticated user
        credentials: JWT token from Authorization header
        session: Database session

    Returns:
        Success message
    """
    try:
        # Get current token JTI
        payload = auth_utils.verify_token(credentials.credentials)
        token_jti = payload.get("jti")

        if logout_data.revoke_all_sessions:
            # Revoke all user sessions
            statement = select(UserSession).where(
                UserSession.user_id == current_user.id, UserSession.is_active == True
            )
            sessions = session.exec(statement).all()

            for user_session in sessions:
                user_session.is_active = False
                session.add(user_session)

            logger.info(f"All sessions revoked for user: {current_user.username}")
        else:
            # Revoke only current session
            await auth_utils.revoke_user_session(session, token_jti)
            logger.info(f"Session revoked for user: {current_user.username}")

        session.commit()

        return {"message": "Logout successful", "success": True}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile information.

    Args:
        current_user: Current authenticated user

    Returns:
        User profile data
    """
    return UserProfileResponse.from_orm(current_user)


@router.put("/me", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Update current user profile.

    Args:
        profile_data: Profile update data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated user profile
    """
    try:
        # Update allowed fields
        allowed_fields = {"chat_settings", "privacy_settings"}

        for field, value in profile_data.items():
            if field in allowed_fields:
                setattr(current_user, field, value)

        current_user.updated_at = datetime.now()
        session.add(current_user)
        session.commit()
        session.refresh(current_user)

        logger.info(f"Profile updated for user: {current_user.username}")

        return UserProfileResponse.from_orm(current_user)

    except Exception as e:
        logger.error(f"Profile update error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed",
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Change user password.

    Args:
        password_data: Password change data
        current_user: Current authenticated user
        session: Database session

    Returns:
        Success message
    """
    try:
        # Verify current password
        if not auth_utils.verify_password(
            password_data.current_password, current_user.hashed_password
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        # Update password
        current_user.hashed_password = auth_utils.get_password_hash(
            password_data.new_password
        )
        current_user.updated_at = datetime.now()
        session.add(current_user)
        session.commit()

        logger.info(f"Password changed for user: {current_user.username}")

        return {"message": "Password changed successfully", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed",
        )


@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get user's active sessions.

    Args:
        current_user: Current authenticated user
        session: Database session

    Returns:
        List of active user sessions
    """
    statement = (
        select(UserSession)
        .where(UserSession.user_id == current_user.id, UserSession.is_active == True)
        .order_by(UserSession.created_at.desc())
    )

    sessions = session.exec(statement).all()
    return [UserSessionResponse.from_orm(s) for s in sessions]


@router.delete("/sessions/{session_id}")
async def revoke_user_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Revoke a specific user session.

    Args:
        session_id: Session ID to revoke
        current_user: Current authenticated user
        session: Database session

    Returns:
        Success message
    """
    try:
        # Find and revoke session
        statement = select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
            UserSession.is_active == True,
        )
        user_session = session.exec(statement).first()

        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        user_session.is_active = False
        session.add(user_session)
        session.commit()

        logger.info(f"Session {session_id} revoked for user: {current_user.username}")

        return {"message": "Session revoked successfully", "success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session revocation error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session revocation failed",
        )
