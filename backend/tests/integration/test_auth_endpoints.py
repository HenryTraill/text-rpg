"""
Integration tests for authentication API endpoints.

Tests complete authentication flow including:
- User registration and validation
- Login and token generation
- Token refresh mechanism
- Logout and session management
- Password changes and profile updates
- Session listing and revocation
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4

from app.main import app
from app.core.auth import auth_utils
from app.models.user import User, UserRole, UserStatus


class TestAuthEndpoints:
    """Integration tests for authentication endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_user_data(self):
        """Sample user registration data."""
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "password_confirm": "TestPassword123!",
        }

    @pytest.fixture
    def sample_login_data(self):
        """Sample login data."""
        return {"username": "testuser", "password": "TestPassword123!"}

    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        return User(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            hashed_password=auth_utils.get_password_hash("TestPassword123!"),
            role=UserRole.PLAYER,
            status=UserStatus.ACTIVE,
            is_verified=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def test_register_user_success(self, client, sample_user_data):
        """Test successful user registration."""
        with patch("app.routers.auth.get_session") as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils:

            # Mock database session
            mock_session = Mock()
            mock_get_session.return_value = mock_session

            # Mock auth utils
            mock_auth_utils.get_user_by_username = AsyncMock(return_value=None)
            mock_auth_utils.get_user_by_email = AsyncMock(return_value=None)
            mock_auth_utils.get_password_hash.return_value = "hashed_password"
            mock_auth_utils.create_access_token.return_value = "access_token"
            mock_auth_utils.create_refresh_token.return_value = "refresh_token"
            mock_auth_utils.verify_token.return_value = {
                "jti": "token_jti",
                "exp": 1234567890,
            }
            mock_auth_utils.create_user_session = AsyncMock()

            response = client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Registration successful"
        assert "user" in data
        assert "tokens" in data
        assert data["tokens"]["access_token"] == "access_token"
        assert data["tokens"]["refresh_token"] == "refresh_token"

    def test_register_user_username_exists(self, client, sample_user_data, mock_user):
        """Test registration with existing username."""
        with patch("app.routers.auth.get_session") as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils:

            mock_session = Mock()
            mock_get_session.return_value = mock_session
            mock_auth_utils.get_user_by_username = AsyncMock(return_value=mock_user)

            response = client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == 400
        data = response.json()
        assert "Username already exists" in data["detail"]

    def test_register_user_email_exists(self, client, sample_user_data, mock_user):
        """Test registration with existing email."""
        with patch("app.routers.auth.get_session") as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils:

            mock_session = Mock()
            mock_get_session.return_value = mock_session
            mock_auth_utils.get_user_by_username = AsyncMock(return_value=None)
            mock_auth_utils.get_user_by_email = AsyncMock(return_value=mock_user)

            response = client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == 400
        data = response.json()
        assert "Email already registered" in data["detail"]

    def test_register_user_invalid_data(self, client):
        """Test registration with invalid data."""
        invalid_data = {
            "username": "ab",  # Too short
            "email": "invalid-email",
            "password": "weak",
            "password_confirm": "different",
        }

        response = client.post("/api/v1/auth/register", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_login_user_success(self, client, sample_login_data, mock_user):
        """Test successful user login."""
        with patch("app.routers.auth.get_session") as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils:

            mock_session = Mock()
            mock_get_session.return_value = mock_session

            mock_auth_utils.authenticate_user = AsyncMock(return_value=mock_user)
            mock_auth_utils.create_access_token.return_value = "access_token"
            mock_auth_utils.create_refresh_token.return_value = "refresh_token"
            mock_auth_utils.verify_token.return_value = {
                "jti": "token_jti",
                "exp": 1234567890,
            }
            mock_auth_utils.create_user_session = AsyncMock()

            response = client.post("/api/v1/auth/login", json=sample_login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Login successful"
        assert "user" in data
        assert "tokens" in data

    def test_login_user_invalid_credentials(self, client, sample_login_data):
        """Test login with invalid credentials."""
        with patch("app.routers.auth.get_session") as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils:

            mock_session = Mock()
            mock_get_session.return_value = mock_session
            mock_auth_utils.authenticate_user = AsyncMock(return_value=None)

            response = client.post("/api/v1/auth/login", json=sample_login_data)

        assert response.status_code == 401
        data = response.json()
        assert "Incorrect username or password" in data["detail"]

    def test_login_user_inactive_account(self, client, sample_login_data, mock_user):
        """Test login with inactive account."""
        mock_user.status = UserStatus.SUSPENDED

        with patch("app.routers.auth.get_session") as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils:

            mock_session = Mock()
            mock_get_session.return_value = mock_session
            mock_auth_utils.authenticate_user = AsyncMock(return_value=mock_user)

            response = client.post("/api/v1/auth/login", json=sample_login_data)

        assert response.status_code == 401
        data = response.json()
        assert "Account is not active" in data["detail"]

    def test_refresh_token_success(self, client, mock_user):
        """Test successful token refresh."""
        refresh_data = {"refresh_token": "valid_refresh_token"}

        with patch("app.routers.auth.get_session") as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils:

            mock_session = Mock()
            mock_get_session.return_value = mock_session

            mock_auth_utils.verify_token.return_value = {
                "type": "refresh",
                "sub": str(mock_user.id),
            }
            mock_auth_utils.get_user_by_id = AsyncMock(return_value=mock_user)
            mock_auth_utils.create_access_token.return_value = "new_access_token"
            mock_auth_utils.create_refresh_token.return_value = "new_refresh_token"
            mock_auth_utils.create_user_session = AsyncMock()

            response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new_access_token"
        assert data["refresh_token"] == "new_refresh_token"

    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid token."""
        refresh_data = {"refresh_token": "invalid_token"}

        with patch("app.routers.auth.get_session") as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils:

            mock_session = Mock()
            mock_get_session.return_value = mock_session

            from fastapi import HTTPException

            mock_auth_utils.verify_token.side_effect = HTTPException(
                status_code=401, detail="Invalid token"
            )

            response = client.post("/api/v1/auth/refresh", json=refresh_data)

        assert response.status_code == 401

    def test_get_current_user_profile(self, client, mock_user):
        """Test getting current user profile."""
        with patch("app.routers.auth.get_current_user", return_value=mock_user):
            response = client.get(
                "/api/v1/auth/me", headers={"Authorization": "Bearer valid_token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == mock_user.username
        assert data["email"] == mock_user.email
        assert data["role"] == mock_user.role

    def test_get_current_user_profile_unauthorized(self, client):
        """Test getting profile without authentication."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # No Authorization header

    def test_update_user_profile(self, client, mock_user):
        """Test updating user profile."""
        update_data = {
            "chat_settings": {"notifications": True},
            "privacy_settings": {"show_online": False},
        }

        with patch("app.routers.auth.get_current_user", return_value=mock_user), patch(
            "app.routers.auth.get_session"
        ) as mock_get_session:

            mock_session = Mock()
            mock_get_session.return_value = mock_session

            response = client.put(
                "/api/v1/auth/me",
                json=update_data,
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["chat_settings"] == update_data["chat_settings"]
        assert data["privacy_settings"] == update_data["privacy_settings"]

    def test_change_password_success(self, client, mock_user):
        """Test successful password change."""
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!",
        }

        with patch("app.routers.auth.get_current_user", return_value=mock_user), patch(
            "app.routers.auth.get_session"
        ) as mock_get_session, patch("app.routers.auth.auth_utils") as mock_auth_utils:

            mock_session = Mock()
            mock_get_session.return_value = mock_session
            mock_auth_utils.verify_password.return_value = True
            mock_auth_utils.get_password_hash.return_value = "new_hashed_password"

            response = client.post(
                "/api/v1/auth/change-password",
                json=password_data,
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Password changed successfully" in data["message"]

    def test_change_password_wrong_current(self, client, mock_user):
        """Test password change with wrong current password."""
        password_data = {
            "current_password": "WrongPassword",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!",
        }

        with patch("app.routers.auth.get_current_user", return_value=mock_user), patch(
            "app.routers.auth.get_session"
        ) as mock_get_session, patch("app.routers.auth.auth_utils") as mock_auth_utils:

            mock_session = Mock()
            mock_get_session.return_value = mock_session
            mock_auth_utils.verify_password.return_value = False

            response = client.post(
                "/api/v1/auth/change-password",
                json=password_data,
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 400
        data = response.json()
        assert "Current password is incorrect" in data["detail"]

    def test_logout_current_session(self, client, mock_user):
        """Test logout of current session."""
        logout_data = {"revoke_all_sessions": False}

        with patch("app.routers.auth.get_current_user", return_value=mock_user), patch(
            "app.routers.auth.get_session"
        ) as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils, patch(
            "app.routers.auth.security"
        ) as mock_security:

            mock_session = Mock()
            mock_get_session.return_value = mock_session

            mock_credentials = Mock()
            mock_credentials.credentials = "valid_token"
            mock_security.return_value = mock_credentials

            mock_auth_utils.verify_token.return_value = {"jti": "token_jti"}
            mock_auth_utils.revoke_user_session = AsyncMock()

            response = client.post(
                "/api/v1/auth/logout",
                json=logout_data,
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Logout successful" in data["message"]

    def test_logout_all_sessions(self, client, mock_user):
        """Test logout of all sessions."""
        logout_data = {"revoke_all_sessions": True}

        with patch("app.routers.auth.get_current_user", return_value=mock_user), patch(
            "app.routers.auth.get_session"
        ) as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils, patch(
            "app.routers.auth.security"
        ) as mock_security, patch(
            "app.routers.auth.select"
        ) as mock_select:

            mock_session = Mock()
            mock_get_session.return_value = mock_session

            mock_credentials = Mock()
            mock_credentials.credentials = "valid_token"
            mock_security.return_value = mock_credentials

            mock_auth_utils.verify_token.return_value = {"jti": "token_jti"}

            # Mock user sessions
            mock_user_session = Mock()
            mock_user_session.is_active = True
            mock_session.exec.return_value.all.return_value = [mock_user_session]

            response = client.post(
                "/api/v1/auth/logout",
                json=logout_data,
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_user_sessions(self, client, mock_user):
        """Test getting user's active sessions."""
        with patch("app.routers.auth.get_current_user", return_value=mock_user), patch(
            "app.routers.auth.get_session"
        ) as mock_get_session, patch("app.routers.auth.select") as mock_select:

            mock_session = Mock()
            mock_get_session.return_value = mock_session

            # Mock user sessions
            mock_user_session = Mock()
            mock_user_session.id = uuid4()
            mock_user_session.device_info = "iPhone 12"
            mock_user_session.ip_address = "192.168.1.1"
            mock_user_session.is_active = True
            mock_user_session.created_at = datetime.now()
            mock_user_session.expires_at = datetime.now() + timedelta(minutes=15)
            mock_user_session.last_activity = datetime.now()

            mock_session.exec.return_value.all.return_value = [mock_user_session]

            response = client.get(
                "/api/v1/auth/sessions", headers={"Authorization": "Bearer valid_token"}
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["device_info"] == "iPhone 12"

    def test_revoke_user_session(self, client, mock_user):
        """Test revoking a specific user session."""
        session_id = uuid4()

        with patch("app.routers.auth.get_current_user", return_value=mock_user), patch(
            "app.routers.auth.get_session"
        ) as mock_get_session, patch("app.routers.auth.select") as mock_select:

            mock_session = Mock()
            mock_get_session.return_value = mock_session

            # Mock user session
            mock_user_session = Mock()
            mock_user_session.id = session_id
            mock_user_session.is_active = True
            mock_session.exec.return_value.first.return_value = mock_user_session

            response = client.delete(
                f"/api/v1/auth/sessions/{session_id}",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Session revoked successfully" in data["message"]

    def test_revoke_user_session_not_found(self, client, mock_user):
        """Test revoking a non-existent session."""
        session_id = uuid4()

        with patch("app.routers.auth.get_current_user", return_value=mock_user), patch(
            "app.routers.auth.get_session"
        ) as mock_get_session, patch("app.routers.auth.select") as mock_select:

            mock_session = Mock()
            mock_get_session.return_value = mock_session
            mock_session.exec.return_value.first.return_value = None

            response = client.delete(
                f"/api/v1/auth/sessions/{session_id}",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 404
        data = response.json()
        assert "Session not found" in data["detail"]


class TestAuthenticationFlow:
    """Integration tests for complete authentication flow."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_complete_auth_flow(self, client):
        """Test complete authentication flow from registration to logout."""
        # Mock all auth operations
        with patch("app.routers.auth.get_session") as mock_get_session, patch(
            "app.routers.auth.auth_utils"
        ) as mock_auth_utils, patch("app.routers.auth.security") as mock_security:

            mock_session = Mock()
            mock_get_session.return_value = mock_session

            # 1. Register user
            mock_auth_utils.get_user_by_username = AsyncMock(return_value=None)
            mock_auth_utils.get_user_by_email = AsyncMock(return_value=None)
            mock_auth_utils.get_password_hash.return_value = "hashed_password"
            mock_auth_utils.create_access_token.return_value = "access_token"
            mock_auth_utils.create_refresh_token.return_value = "refresh_token"
            mock_auth_utils.verify_token.return_value = {
                "jti": "token_jti",
                "exp": 1234567890,
            }
            mock_auth_utils.create_user_session = AsyncMock()

            register_data = {
                "username": "flowtest",
                "email": "flowtest@example.com",
                "password": "FlowTest123!",
                "password_confirm": "FlowTest123!",
            }

            register_response = client.post("/api/v1/auth/register", json=register_data)
            assert register_response.status_code == 200

            # 2. Login user
            mock_user = Mock()
            mock_user.id = uuid4()
            mock_user.username = "flowtest"
            mock_user.status = UserStatus.ACTIVE

            mock_auth_utils.authenticate_user = AsyncMock(return_value=mock_user)

            login_data = {"username": "flowtest", "password": "FlowTest123!"}

            login_response = client.post("/api/v1/auth/login", json=login_data)
            assert login_response.status_code == 200

            # 3. Get profile
            mock_current_user = Mock()
            mock_current_user.username = "flowtest"
            mock_current_user.email = "flowtest@example.com"
            mock_current_user.role = UserRole.PLAYER

            with patch(
                "app.routers.auth.get_current_user", return_value=mock_current_user
            ):
                profile_response = client.get(
                    "/api/v1/auth/me", headers={"Authorization": "Bearer access_token"}
                )
                assert profile_response.status_code == 200

            # 4. Logout
            mock_credentials = Mock()
            mock_credentials.credentials = "access_token"
            mock_security.return_value = mock_credentials
            mock_auth_utils.revoke_user_session = AsyncMock()

            with patch(
                "app.routers.auth.get_current_user", return_value=mock_current_user
            ):
                logout_response = client.post(
                    "/api/v1/auth/logout",
                    json={"revoke_all_sessions": False},
                    headers={"Authorization": "Bearer access_token"},
                )
                assert logout_response.status_code == 200
