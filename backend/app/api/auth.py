"""
Authentication API routes.

This module provides HTTP endpoints for:
- User registration and login
- JWT token management (access/refresh)
- Password management
- Session management
- Account verification
"""

from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session, select
from uuid import UUID

from ..core.database import get_session
from ..core.dependencies import (
    get_current_user,
    get_current_user_optional,
    verify_refresh_token,
    apply_rate_limit,
    security
)
from ..core.security import (
    create_password_hash,
    verify_password,
    create_token_pair,
    verify_token
)
from ..core.rate_limiting import add_rate_limit_headers
from ..models.user import User, UserSession, UserStatus, UserRole
from .auth_schemas import (
    UserRegistrationRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordChangeRequest,
    UserResponse,
    UserProfileUpdate,
    SessionInfo,
    AuthErrorResponse,
    RateLimitResponse
)

# Create router
router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
    description="Create a new user account with username, email, and password validation"
)
async def register_user(
    request: Request,
    user_data: UserRegistrationRequest,
    session: Session = Depends(get_session),
    rate_limit: dict = Depends(lambda r: apply_rate_limit(r, limit=10, window=300))  # 10 registrations per 5 minutes
):
    """
    Register a new user account.
    
    - **username**: Unique username (3-30 characters, alphanumeric and underscores)
    - **email**: Valid email address (must be unique)
    - **password**: Strong password (minimum 8 characters with letter and number)
    - **confirm_password**: Must match password
    """
    
    # Check if username already exists
    existing_user = session.exec(
        select(User).where(User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()
    
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=create_password_hash(user_data.password),
        status=UserStatus.ACTIVE,  # For now, skip email verification
        is_verified=True,  # For now, auto-verify
        role=UserRole.PLAYER
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return UserResponse.from_orm(new_user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and return JWT tokens"
)
async def login_user(
    request: Request,
    response: Response,
    login_data: UserLoginRequest,
    session: Session = Depends(get_session),
    rate_limit: dict = Depends(lambda r: apply_rate_limit(r, limit=20, window=300))  # 20 login attempts per 5 minutes
):
    """
    Authenticate user and return access/refresh tokens.
    
    - **username**: Username or email address
    - **password**: User password
    - **remember_me**: Extend session duration
    - **device_info**: Optional device information for session tracking
    """
    
    # Find user by username or email
    user = session.exec(
        select(User).where(
            (User.username == login_data.username.lower()) |
            (User.email == login_data.username.lower())
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account temporarily locked due to too many failed attempts"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        # Increment failed login attempts
        user.login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if user.login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        
        session.add(user)
        session.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check account status
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.value}"
        )
    
    # Reset login attempts on successful login
    user.login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    
    # Create token pair
    tokens = create_token_pair(str(user.id), user.username)
    
    # Create session record
    session_expires = datetime.now(timezone.utc) + timedelta(days=7 if login_data.remember_me else 1)
    user_session = UserSession(
        user_id=user.id,
        token_jti=verify_token(tokens.refresh_token, "refresh").jti,
        device_info=login_data.device_info,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        expires_at=session_expires
    )
    
    session.add(user)
    session.add(user_session)
    session.commit()
    session.refresh(user)
    
    # Add rate limit headers
    await add_rate_limit_headers(response, rate_limit)
    
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=UserResponse.from_orm(user)
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Use refresh token to get new access token"
)
async def refresh_token(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    user_and_jti: tuple = Depends(verify_refresh_token),
    rate_limit: dict = Depends(lambda r: apply_rate_limit(r, limit=50, window=300))  # 50 refreshes per 5 minutes
):
    """
    Refresh access token using valid refresh token.
    
    Returns new access token and optionally new refresh token.
    """
    
    user, old_jti = user_and_jti
    
    # Create new token pair
    tokens = create_token_pair(str(user.id), user.username)
    
    # Update session with new refresh token JTI
    statement = select(UserSession).where(
        UserSession.user_id == user.id,
        UserSession.token_jti == old_jti,
        UserSession.is_active == True
    )
    user_session = session.exec(statement).first()
    
    if user_session:
        user_session.token_jti = verify_token(tokens.refresh_token, "refresh").jti
        user_session.last_activity = datetime.now(timezone.utc)
        session.add(user_session)
        session.commit()
    
    # Add rate limit headers
    await add_rate_limit_headers(response, rate_limit)
    
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=UserResponse.from_orm(user)
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User logout",
    description="Invalidate current session and refresh token"
)
async def logout_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Logout user by invalidating the current session.
    
    This will deactivate the refresh token associated with the current session.
    """
    
    if credentials:
        try:
            # Get JTI from access token to find associated refresh token session
            token_data = verify_token(credentials.credentials, "access")
            
            # Find and deactivate the session
            # Note: This is a simplified approach. In production, you might want to
            # maintain a mapping between access token JTI and refresh token JTI
            statement = select(UserSession).where(
                UserSession.user_id == current_user.id,
                UserSession.is_active == True
            )
            sessions = session.exec(statement).all()
            
            # Deactivate the most recent session (could be improved with better tracking)
            if sessions:
                latest_session = max(sessions, key=lambda s: s.last_activity)
                latest_session.is_active = False
                session.add(latest_session)
                session.commit()
                
        except Exception:
            # Even if token parsing fails, we'll still return success
            # This prevents information leakage about token validity
            pass
    
    return None


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get authenticated user's profile information"
)
async def get_current_user_profile(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    rate_limit: dict = Depends(apply_rate_limit)
):
    """
    Get current authenticated user's profile information.
    """
    
    # Add rate limit headers
    await add_rate_limit_headers(response, rate_limit)
    
    return UserResponse.from_orm(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update authenticated user's profile information"
)
async def update_current_user_profile(
    request: Request,
    response: Response,
    profile_data: UserProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    rate_limit: dict = Depends(lambda r: apply_rate_limit(r, limit=20, window=300))  # 20 updates per 5 minutes
):
    """
    Update current authenticated user's profile information.
    
    - **email**: New email address (must be unique)
    - **chat_settings**: Chat preferences and settings
    - **privacy_settings**: Privacy preferences
    """
    
    # Check if new email is already taken
    if profile_data.email and profile_data.email != current_user.email:
        existing_email = session.exec(
            select(User).where(
                User.email == profile_data.email,
                User.id != current_user.id
            )
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered to another account"
            )
        
        current_user.email = profile_data.email
        current_user.is_verified = False  # Require re-verification for new email
    
    # Update settings
    if profile_data.chat_settings is not None:
        current_user.chat_settings = profile_data.chat_settings
    
    if profile_data.privacy_settings is not None:
        current_user.privacy_settings = profile_data.privacy_settings
    
    current_user.updated_at = datetime.now(timezone.utc)
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    # Add rate limit headers
    await add_rate_limit_headers(response, rate_limit)
    
    return UserResponse.from_orm(current_user)


@router.get(
    "/sessions",
    response_model=List[SessionInfo],
    summary="Get user sessions",
    description="Get list of active sessions for the authenticated user"
)
async def get_user_sessions(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    rate_limit: dict = Depends(apply_rate_limit)
):
    """
    Get list of active sessions for the authenticated user.
    
    This can be used to show the user where they are logged in
    and allow them to terminate sessions from other devices.
    """
    
    statement = select(UserSession).where(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    )
    user_sessions = session.exec(statement).all()
    
    # Add rate limit headers
    await add_rate_limit_headers(response, rate_limit)
    
    return [SessionInfo.from_orm(s) for s in user_sessions]


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Terminate user session",
    description="Terminate a specific user session by ID"
)
async def terminate_user_session(
    session_id: UUID,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Terminate a specific user session.
    
    This will invalidate the refresh token associated with that session.
    """
    
    statement = select(UserSession).where(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    )
    user_session = session.exec(statement).first()
    
    if not user_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    user_session.is_active = False
    session.add(user_session)
    session.commit()
    
    return None


@router.post(
    "/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change user password",
    description="Change the authenticated user's password"
)
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    rate_limit: dict = Depends(lambda r: apply_rate_limit(r, limit=5, window=300))  # 5 password changes per 5 minutes
):
    """
    Change the authenticated user's password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters with letter and number)
    - **confirm_new_password**: Must match new password
    """
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = create_password_hash(password_data.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    
    # Invalidate all existing sessions except current one
    statement = select(UserSession).where(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    )
    user_sessions = session.exec(statement).all()
    
    for user_session in user_sessions:
        user_session.is_active = False
        session.add(user_session)
    
    session.add(current_user)
    session.commit()
    
    return None