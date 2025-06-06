"""
Unit tests for authentication utilities.

Tests core authentication functionality including:
- Password hashing and verification
- JWT token creation and validation
- User authentication and session management
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from jose import jwt

from app.core.auth import AuthUtils, auth_utils
from app.core.config import settings
from app.models.user import User, UserSession, UserStatus, UserRole


class TestAuthUtils:
    """Test suite for AuthUtils class."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPassword123!"
        
        # Test password hashing
        hashed = AuthUtils.get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are typically 60 characters
        
        # Test password verification
        assert AuthUtils.verify_password(password, hashed)
        assert not AuthUtils.verify_password("WrongPassword", hashed)
        assert not AuthUtils.verify_password("", hashed)
    
    def test_access_token_creation(self):
        """Test JWT access token creation."""
        user_data = {"sub": str(uuid4()), "username": "testuser"}
        expires_delta = timedelta(minutes=15)
        
        token = AuthUtils.create_access_token(user_data, expires_delta)
        
        # Verify token structure
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT has 3 parts
        
        # Decode and verify payload
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == user_data["sub"]
        assert payload["username"] == user_data["username"]
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
        
        # Verify expiration is correct
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        assert (exp_time - iat_time) <= expires_delta + timedelta(seconds=1)  # Allow 1s tolerance
    
    def test_refresh_token_creation(self):
        """Test JWT refresh token creation."""
        user_data = {"sub": str(uuid4())}
        expires_delta = timedelta(days=7)
        
        token = AuthUtils.create_refresh_token(user_data, expires_delta)
        
        # Verify token structure
        assert isinstance(token, str)
        assert len(token.split('.')) == 3
        
        # Decode and verify payload
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == user_data["sub"]
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload
    
    def test_token_verification_valid(self):
        """Test JWT token verification with valid token."""
        user_data = {"sub": str(uuid4()), "username": "testuser"}
        token = AuthUtils.create_access_token(user_data)
        
        payload = AuthUtils.verify_token(token)
        
        assert payload["sub"] == user_data["sub"]
        assert payload["username"] == user_data["username"]
        assert "exp" in payload
        assert "jti" in payload
    
    def test_token_verification_expired(self):
        """Test JWT token verification with expired token."""
        user_data = {"sub": str(uuid4())}
        expired_token = AuthUtils.create_access_token(
            user_data, 
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            AuthUtils.verify_token(expired_token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
    
    def test_token_verification_invalid(self):
        """Test JWT token verification with invalid token."""
        from fastapi import HTTPException
        
        # Test with malformed token
        with pytest.raises(HTTPException) as exc_info:
            AuthUtils.verify_token("invalid.token.here")
        
        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()
        
        # Test with wrong secret
        user_data = {"sub": str(uuid4())}
        token = jwt.encode(user_data, "wrong_secret", algorithm=settings.algorithm)
        
        with pytest.raises(HTTPException) as exc_info:
            AuthUtils.verify_token(token)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_user_by_username(self):
        """Test getting user by username."""
        mock_session = Mock()
        mock_result = Mock()
        mock_user = Mock()
        
        mock_session.exec.return_value = mock_result
        mock_result.first.return_value = mock_user
        
        result = await AuthUtils.get_user_by_username(mock_session, "testuser")
        
        assert result == mock_user
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self):
        """Test getting user by email."""
        mock_session = Mock()
        mock_result = Mock()
        mock_user = Mock()
        
        mock_session.exec.return_value = mock_result
        mock_result.first.return_value = mock_user
        
        result = await AuthUtils.get_user_by_email(mock_session, "test@example.com")
        
        assert result == mock_user
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self):
        """Test getting user by ID."""
        mock_session = Mock()
        mock_result = Mock()
        mock_user = Mock()
        user_id = uuid4()
        
        mock_session.exec.return_value = mock_result
        mock_result.first.return_value = mock_user
        
        result = await AuthUtils.get_user_by_id(mock_session, user_id)
        
        assert result == mock_user
        mock_session.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication."""
        mock_session = Mock()
        password = "TestPassword123!"
        hashed_password = AuthUtils.get_password_hash(password)
        
        mock_user = Mock()
        mock_user.hashed_password = hashed_password
        
        with patch.object(AuthUtils, 'get_user_by_username', return_value=mock_user):
            result = await AuthUtils.authenticate_user(mock_session, "testuser", password)
            
        assert result == mock_user
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Test user authentication with wrong password."""
        mock_session = Mock()
        password = "TestPassword123!"
        wrong_password = "WrongPassword"
        hashed_password = AuthUtils.get_password_hash(password)
        
        mock_user = Mock()
        mock_user.hashed_password = hashed_password
        
        with patch.object(AuthUtils, 'get_user_by_username', return_value=mock_user):
            result = await AuthUtils.authenticate_user(mock_session, "testuser", wrong_password)
            
        assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """Test user authentication with non-existent user."""
        mock_session = Mock()
        
        with patch.object(AuthUtils, 'get_user_by_username', return_value=None):
            result = await AuthUtils.authenticate_user(mock_session, "nonexistent", "password")
            
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_user_session(self):
        """Test creating a user session."""
        mock_session = Mock()
        user_id = uuid4()
        token_jti = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        result = await AuthUtils.create_user_session(
            session=mock_session,
            user_id=user_id,
            token_jti=token_jti,
            expires_at=expires_at,
            device_info="Test Device",
            ip_address="127.0.0.1",
            user_agent="Test Agent"
        )
        
        assert isinstance(result, UserSession)
        assert result.user_id == user_id
        assert result.token_jti == token_jti
        assert result.expires_at == expires_at
        assert result.device_info == "Test Device"
        assert result.ip_address == "127.0.0.1"
        assert result.user_agent == "Test Agent"
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_user_session_success(self):
        """Test successful session revocation."""
        mock_session = Mock()
        mock_result = Mock()
        mock_user_session = Mock()
        mock_user_session.is_active = True
        token_jti = str(uuid4())
        
        mock_session.exec.return_value = mock_result
        mock_result.first.return_value = mock_user_session
        
        result = await AuthUtils.revoke_user_session(mock_session, token_jti)
        
        assert result is True
        assert mock_user_session.is_active is False
        mock_session.add.assert_called_once_with(mock_user_session)
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_user_session_not_found(self):
        """Test session revocation when session not found."""
        mock_session = Mock()
        mock_result = Mock()
        token_jti = str(uuid4())
        
        mock_session.exec.return_value = mock_result
        mock_result.first.return_value = None
        
        result = await AuthUtils.revoke_user_session(mock_session, token_jti)
        
        assert result is False
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_is_token_revoked_active(self):
        """Test checking if token is revoked for active token."""
        mock_session = Mock()
        mock_result = Mock()
        mock_user_session = Mock()
        token_jti = str(uuid4())
        
        mock_session.exec.return_value = mock_result
        mock_result.first.return_value = mock_user_session
        
        result = await AuthUtils.is_token_revoked(mock_session, token_jti)
        
        assert result is False  # Token is active, so not revoked
    
    @pytest.mark.asyncio
    async def test_is_token_revoked_inactive(self):
        """Test checking if token is revoked for inactive token."""
        mock_session = Mock()
        mock_result = Mock()
        token_jti = str(uuid4())
        
        mock_session.exec.return_value = mock_result
        mock_result.first.return_value = None  # No active session found
        
        result = await AuthUtils.is_token_revoked(mock_session, token_jti)
        
        assert result is True  # No active session means token is revoked


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password=AuthUtils.get_password_hash("TestPassword123!"),
        role=UserRole.PLAYER,
        status=UserStatus.ACTIVE,
        is_verified=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_session(sample_user):
    """Create a sample user session for testing."""
    return UserSession(
        id=uuid4(),
        user_id=sample_user.id,
        token_jti=str(uuid4()),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        is_active=True,
        created_at=datetime.now(),
        last_activity=datetime.now()
    ) 