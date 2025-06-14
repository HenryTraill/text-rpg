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
        import time

        timestamp = int(time.time())
        return {
            "username": f"testuser_{timestamp}",
            "email": f"test_{timestamp}@example.com",
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
        with (
            patch("app.routers.auth.get_session") as mock_get_session,
            patch("app.routers.auth.auth_utils") as mock_auth_utils,
        ):
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
        with (
            patch("app.routers.auth.get_session") as mock_get_session,
            patch("app.routers.auth.auth_utils") as mock_auth_utils,
        ):
            mock_session = Mock()
            mock_get_session.return_value = mock_session
            mock_auth_utils.get_user_by_username = AsyncMock(return_value=mock_user)

            response = client.post("/api/v1/auth/register", json=sample_user_data)

        assert response.status_code == 400
        data = response.json()
        assert "Username already exists" in data["detail"]

    def test_register_user_email_exists(self, client, sample_user_data, mock_user):
        """Test registration with existing email."""
        with (
            patch("app.routers.auth.get_session") as mock_get_session,
            patch("app.routers.auth.auth_utils") as mock_auth_utils,
        ):
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
        with (
            patch("app.routers.auth.get_session") as mock_get_session,
            patch("app.routers.auth.auth_utils") as mock_auth_utils,
        ):
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
        with (
            patch("app.routers.auth.get_session") as mock_get_session,
            patch("app.routers.auth.auth_utils") as mock_auth_utils,
        ):
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

        with (
            patch("app.routers.auth.get_session") as mock_get_session,
            patch("app.routers.auth.auth_utils") as mock_auth_utils,
        ):
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

        with (
            patch("app.routers.auth.get_session") as mock_get_session,
            patch("app.routers.auth.auth_utils") as mock_auth_utils,
        ):
            mock_session = Mock()
            mock_get_session.return_value = mock_session

            import time
            mock_auth_utils.verify_token.return_value = {
                "type": "refresh",
                "sub": str(mock_user.id),
                "jti": "refresh_token_jti",
                "exp": int(time.time()) + 3600,  # Expires in 1 hour
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

        with (
            patch("app.routers.auth.get_session") as mock_get_session,
            patch("app.routers.auth.auth_utils") as mock_auth_utils,
        ):
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
        from app.routers.auth import get_current_user
        from app.main import app
        
        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            response = client.get(
                "/api/v1/auth/me", headers={"Authorization": "Bearer valid_token"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["username"] == mock_user.username
            assert data["email"] == mock_user.email
            assert data["role"] == mock_user.role
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_get_current_user_profile_unauthorized(self, client):
        """Test getting profile without authentication."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # No Authorization header

    def test_update_user_profile(self, client, mock_user):
        """Test updating user profile."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        update_data = {
            "chat_settings": {"notifications": True},
            "privacy_settings": {"show_online": False},
        }

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            response = client.put(
                "/api/v1/auth/me",
                json=update_data,
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["chat_settings"] == update_data["chat_settings"]
            assert data["privacy_settings"] == update_data["privacy_settings"]
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_change_password_success(self, client, mock_user):
        """Test successful password change."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!",
        }

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.auth_utils") as mock_auth_utils,
            ):
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
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_change_password_wrong_current(self, client, mock_user):
        """Test password change with wrong current password."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        password_data = {
            "current_password": "WrongPassword",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!",
        }

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.auth_utils") as mock_auth_utils,
            ):
                mock_auth_utils.verify_password.return_value = False

                response = client.post(
                    "/api/v1/auth/change-password",
                    json=password_data,
                    headers={"Authorization": "Bearer valid_token"},
                )

            assert response.status_code == 400
            data = response.json()
            assert "Current password is incorrect" in data["detail"]
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_logout_current_session(self, client, mock_user):
        """Test logout of current session."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        logout_data = {"revoke_all_sessions": False}

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.auth_utils") as mock_auth_utils,
                patch("app.routers.auth.security") as mock_security,
            ):
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
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_logout_all_sessions(self, client, mock_user):
        """Test logout of all sessions."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        logout_data = {"revoke_all_sessions": True}

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.auth_utils") as mock_auth_utils,
                patch("app.routers.auth.security") as mock_security,
                patch("app.routers.auth.select"),
            ):
                mock_credentials = Mock()
                mock_credentials.credentials = "valid_token"
                mock_security.return_value = mock_credentials

                mock_auth_utils.verify_token.return_value = {"jti": "token_jti"}

                response = client.post(
                    "/api/v1/auth/logout",
                    json=logout_data,
                    headers={"Authorization": "Bearer valid_token"},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_get_user_sessions(self, client, mock_user):
        """Test getting user's active sessions."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.select"),
            ):
                response = client.get(
                    "/api/v1/auth/sessions", headers={"Authorization": "Bearer valid_token"}
                )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_revoke_user_session(self, client, mock_user):
        """Test revoking a specific user session."""
        from app.routers.auth import get_current_user
        from app.main import app
        from app.core.database import get_session
        
        session_id = uuid4()

        # Create a mock session object
        mock_user_session = Mock()
        mock_user_session.id = session_id
        mock_user_session.user_id = mock_user.id
        mock_user_session.is_active = True

        # Create mock database session
        mock_db_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalars.return_value.first.return_value = mock_user_session
        mock_db_session.execute.return_value = mock_result
        
        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_session] = lambda: mock_db_session
        
        try:
            response = client.delete(
                f"/api/v1/auth/sessions/{session_id}",
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Session revoked successfully" in data["message"]
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]
            if get_session in app.dependency_overrides:
                del app.dependency_overrides[get_session]

    def test_revoke_user_session_not_found(self, client, mock_user):
        """Test revoking a non-existent session."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        session_id = uuid4()

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.select"),
            ):
                response = client.delete(
                    f"/api/v1/auth/sessions/{session_id}",
                    headers={"Authorization": "Bearer valid_token"},
                )

            assert response.status_code == 404
            data = response.json()
            assert "Session not found" in data["detail"]
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_login_with_email(self, client, mock_user):
        """Test successful login using email instead of username."""
        email_login_data = {
            "username": "test@example.com",  # Using email in username field
            "password": "TestPassword123!",
        }

        with (
            patch("app.routers.auth.get_session") as mock_get_session,
            patch("app.routers.auth.auth_utils") as mock_auth_utils,
        ):
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

            response = client.post("/api/v1/auth/login", json=email_login_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Login successful"

    def test_login_case_insensitive(self, client, mock_user):
        """Test case-insensitive login with username and email."""
        test_cases = [
            {
                "username": "TESTUSER",
                "password": "TestPassword123!",
            },  # Uppercase username
            {
                "username": "TestUser",
                "password": "TestPassword123!",
            },  # Mixed case username
            {
                "username": "TEST@EXAMPLE.COM",
                "password": "TestPassword123!",
            },  # Uppercase email
            {
                "username": "Test@Example.Com",
                "password": "TestPassword123!",
            },  # Mixed case email
        ]

        for login_data in test_cases:
            with (
                patch("app.routers.auth.get_session") as mock_get_session,
                patch("app.routers.auth.auth_utils") as mock_auth_utils,
            ):
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

                response = client.post("/api/v1/auth/login", json=login_data)

            assert response.status_code == 200, f"Failed for login data: {login_data}"
            data = response.json()
            assert data["success"] is True

    def test_update_profile_username(self, client, mock_user):
        """Test updating user profile username."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        update_data = {"username": "newusername"}

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.auth_utils") as mock_auth_utils,
            ):
                mock_auth_utils.get_user_by_username = AsyncMock(return_value=None)

                response = client.put(
                    "/api/v1/auth/me",
                    json=update_data,
                    headers={"Authorization": "Bearer valid_token"},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "newusername"
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_update_profile_username_already_taken(self, client, mock_user):
        """Test updating username to one that already exists."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        update_data = {"username": "existinguser"}
        existing_user = Mock()

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.auth_utils") as mock_auth_utils,
            ):
                mock_auth_utils.get_user_by_username = AsyncMock(return_value=existing_user)

                response = client.put(
                    "/api/v1/auth/me",
                    json=update_data,
                    headers={"Authorization": "Bearer valid_token"},
                )

            assert response.status_code == 400
            data = response.json()
            assert "Username already taken" in data["detail"]
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_update_profile_email(self, client, mock_user):
        """Test updating user profile email."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        update_data = {"email": "newemail@example.com"}

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.auth_utils") as mock_auth_utils,
            ):
                mock_auth_utils.get_user_by_email = AsyncMock(return_value=None)

                response = client.put(
                    "/api/v1/auth/me",
                    json=update_data,
                    headers={"Authorization": "Bearer valid_token"},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "newemail@example.com"
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_update_profile_email_already_taken(self, client, mock_user):
        """Test updating email to one that already exists."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        update_data = {"email": "existing@example.com"}
        existing_user = Mock()

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.auth_utils") as mock_auth_utils,
            ):
                mock_auth_utils.get_user_by_email = AsyncMock(return_value=existing_user)

                response = client.put(
                    "/api/v1/auth/me",
                    json=update_data,
                    headers={"Authorization": "Bearer valid_token"},
                )

            assert response.status_code == 400
            data = response.json()
            assert "Email already in use by another account" in data["detail"]
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_update_profile_max_characters(self, client, mock_user):
        """Test updating user profile max_characters."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        update_data = {"max_characters": 8}

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            response = client.put(
                "/api/v1/auth/me",
                json=update_data,
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["max_characters"] == 8
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_update_profile_max_characters_invalid(self, client, mock_user):
        """Test updating max_characters with invalid value."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        update_data = {"max_characters": 15}  # Exceeds limit of 10

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            response = client.put(
                "/api/v1/auth/me",
                json=update_data,
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == 422  # Validation error
            data = response.json()
            assert "less than or equal to 10" in str(data["detail"])
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_update_profile_username_invalid_format(self, client, mock_user):
        """Test updating username with invalid format."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        update_data = {"username": "invalid-username!"}  # Contains invalid characters

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            response = client.put(
                "/api/v1/auth/me",
                json=update_data,
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == 422  # Validation error
            data = response.json()
            assert "alphanumeric characters and underscores" in str(data["detail"])
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_update_profile_username_too_short(self, client, mock_user):
        """Test updating username that's too short."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        update_data = {"username": "ab"}  # Less than 3 characters

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            response = client.put(
                "/api/v1/auth/me",
                json=update_data,
                headers={"Authorization": "Bearer valid_token"},
            )

            assert response.status_code == 422  # Validation error
            data = response.json()
            assert "at least 3 characters" in str(data["detail"])
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]

    def test_update_profile_multiple_fields(self, client, mock_user):
        """Test updating multiple profile fields at once."""
        from app.routers.auth import get_current_user
        from app.main import app
        
        update_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "max_characters": 7,
            "chat_settings": {"notifications": True, "sound": False},
            "privacy_settings": {"show_online": False},
        }

        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with (
                patch("app.routers.auth.auth_utils") as mock_auth_utils,
            ):
                mock_auth_utils.get_user_by_username = AsyncMock(return_value=None)
                mock_auth_utils.get_user_by_email = AsyncMock(return_value=None)

                response = client.put(
                    "/api/v1/auth/me",
                    json=update_data,
                    headers={"Authorization": "Bearer valid_token"},
                )

            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "newuser"
            assert data["email"] == "newuser@example.com"
            assert data["max_characters"] == 7
            assert data["chat_settings"] == {"notifications": True, "sound": False}
            assert data["privacy_settings"] == {"show_online": False}
        finally:
            # Clean up
            if get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]


class TestAuthenticationFlow:
    """Integration tests for complete authentication flow."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_complete_auth_flow(self, client):
        """Test complete authentication flow from registration to logout."""
        # Mock all auth operations
        with (
            patch("app.routers.auth.get_session") as mock_get_session,
            patch("app.routers.auth.auth_utils") as mock_auth_utils,
            patch("app.routers.auth.security") as mock_security,
        ):
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
            from datetime import datetime, timezone
            mock_user = Mock()
            mock_user.id = uuid4()
            mock_user.username = "flowtest"
            mock_user.email = "flowtest@example.com"
            mock_user.role = "player"
            mock_user.status = UserStatus.ACTIVE
            mock_user.is_verified = True
            mock_user.created_at = datetime.now(timezone.utc)
            mock_user.max_characters = 5
            mock_user.chat_settings = {}
            mock_user.privacy_settings = {}

            mock_auth_utils.authenticate_user = AsyncMock(return_value=mock_user)

            login_data = {"username": "flowtest", "password": "FlowTest123!"}

            login_response = client.post("/api/v1/auth/login", json=login_data)
            assert login_response.status_code == 200

            # 3. Get profile
            mock_current_user = Mock()
            mock_current_user.id = uuid4()
            mock_current_user.username = "flowtest"
            mock_current_user.email = "flowtest@example.com"
            mock_current_user.role = "player"
            mock_current_user.status = "active"
            mock_current_user.is_verified = True
            mock_current_user.created_at = datetime.now(timezone.utc)
            mock_current_user.updated_at = datetime.now(timezone.utc)
            mock_current_user.last_login = datetime.now(timezone.utc)
            mock_current_user.max_characters = 5
            mock_current_user.chat_settings = {}
            mock_current_user.privacy_settings = {}

            from app.routers.auth import get_current_user
            from app.main import app
            
            # Override the dependency
            app.dependency_overrides[get_current_user] = lambda: mock_current_user
            
            try:
                profile_response = client.get(
                    "/api/v1/auth/me", headers={"Authorization": "Bearer access_token"}
                )
                assert profile_response.status_code == 200

                # 4. Logout
                mock_credentials = Mock()
                mock_credentials.credentials = "access_token"
                mock_security.return_value = mock_credentials
                mock_auth_utils.revoke_user_session = AsyncMock()

                logout_response = client.post(
                    "/api/v1/auth/logout",
                    json={"revoke_all_sessions": False},
                    headers={"Authorization": "Bearer access_token"},
                )
                assert logout_response.status_code == 200
            finally:
                # Clean up
                if get_current_user in app.dependency_overrides:
                    del app.dependency_overrides[get_current_user]
