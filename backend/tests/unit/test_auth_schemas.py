"""
Unit tests for authentication schemas.

Tests Pydantic validation for:
- User registration and login requests
- Token responses
- Password validation
- Input sanitization
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
from uuid import uuid4

from app.schemas.auth import (
    UserRegistrationRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    PasswordChangeRequest,
    UserSessionResponse,
    LogoutRequest,
    AuthenticationResponse,
    ErrorResponse,
)
from app.models.user import UserRole, UserStatus


class TestUserRegistrationRequest:
    """Test user registration request validation."""

    def test_valid_registration(self):
        """Test valid user registration data."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "password_confirm": "TestPassword123!",
        }

        request = UserRegistrationRequest(**data)

        assert request.username == "testuser"
        assert request.email == "test@example.com"
        assert request.password == "TestPassword123!"
        assert request.password_confirm == "TestPassword123!"

    def test_username_lowercase_conversion(self):
        """Test that username is converted to lowercase."""
        data = {
            "username": "TestUser",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "password_confirm": "TestPassword123!",
        }

        request = UserRegistrationRequest(**data)
        assert request.username == "testuser"

    def test_username_validation_short(self):
        """Test username validation for too short username."""
        data = {
            "username": "ab",  # Too short
            "email": "test@example.com",
            "password": "TestPassword123!",
            "password_confirm": "TestPassword123!",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(**data)

        assert "at least 3 characters" in str(exc_info.value)

    def test_username_validation_long(self):
        """Test username validation for too long username."""
        data = {
            "username": "a" * 31,  # Too long
            "email": "test@example.com",
            "password": "TestPassword123!",
            "password_confirm": "TestPassword123!",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(**data)

        assert "at most 30 characters" in str(exc_info.value)

    def test_username_validation_invalid_characters(self):
        """Test username validation for invalid characters."""
        data = {
            "username": "test@user",  # Invalid character
            "email": "test@example.com",
            "password": "TestPassword123!",
            "password_confirm": "TestPassword123!",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(**data)

        assert "alphanumeric characters and underscores" in str(exc_info.value)

    def test_email_validation_invalid(self):
        """Test email validation for invalid email."""
        data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "TestPassword123!",
            "password_confirm": "TestPassword123!",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(**data)

        assert "email" in str(exc_info.value).lower()

    def test_password_validation_too_short(self):
        """Test password validation for too short password."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",
            "password_confirm": "short",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(**data)

        assert "at least 8 characters" in str(exc_info.value)

    def test_password_validation_no_uppercase(self):
        """Test password validation for missing uppercase letter."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123!",
            "password_confirm": "testpassword123!",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(**data)

        assert "uppercase letter" in str(exc_info.value)

    def test_password_validation_no_lowercase(self):
        """Test password validation for missing lowercase letter."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TESTPASSWORD123!",
            "password_confirm": "TESTPASSWORD123!",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(**data)

        assert "lowercase letter" in str(exc_info.value)

    def test_password_validation_no_digit(self):
        """Test password validation for missing digit."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword!",
            "password_confirm": "TestPassword!",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(**data)

        assert "digit" in str(exc_info.value)

    def test_password_mismatch(self):
        """Test password confirmation mismatch."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "password_confirm": "DifferentPassword123!",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegistrationRequest(**data)

        assert "do not match" in str(exc_info.value)


class TestUserLoginRequest:
    """Test user login request validation."""

    def test_valid_login(self):
        """Test valid login data."""
        data = {
            "username": "testuser",
            "password": "TestPassword123!",
            "remember_me": True,
            "device_info": "iPhone 12",
        }

        request = UserLoginRequest(**data)

        assert request.username == "testuser"
        assert request.password == "TestPassword123!"
        assert request.remember_me is True
        assert request.device_info == "iPhone 12"

    def test_minimal_login(self):
        """Test minimal login data with defaults."""
        data = {"username": "testuser", "password": "TestPassword123!"}

        request = UserLoginRequest(**data)

        assert request.username == "testuser"
        assert request.password == "TestPassword123!"
        assert request.remember_me is False
        assert request.device_info is None


class TestTokenResponse:
    """Test token response schema."""

    def test_valid_token_response(self):
        """Test valid token response."""
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "expires_in": 900,
        }

        response = TokenResponse(**data)

        assert response.access_token == data["access_token"]
        assert response.refresh_token == data["refresh_token"]
        assert response.token_type == "bearer"
        assert response.expires_in == 900


class TestPasswordChangeRequest:
    """Test password change request validation."""

    def test_valid_password_change(self):
        """Test valid password change data."""
        data = {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!",
        }

        request = PasswordChangeRequest(**data)

        assert request.current_password == "OldPassword123!"
        assert request.new_password == "NewPassword123!"
        assert request.new_password_confirm == "NewPassword123!"

    def test_new_password_validation(self):
        """Test new password validation."""
        data = {
            "current_password": "OldPassword123!",
            "new_password": "weak",
            "new_password_confirm": "weak",
        }

        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(**data)

        assert "at least 8 characters" in str(exc_info.value)

    def test_new_password_mismatch(self):
        """Test new password confirmation mismatch."""
        data = {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "new_password_confirm": "DifferentPassword123!",
        }

        with pytest.raises(ValidationError) as exc_info:
            PasswordChangeRequest(**data)

        assert "do not match" in str(exc_info.value)


class TestUserResponse:
    """Test user response schema."""

    def test_user_response_creation(self):
        """Test creating user response from data."""
        user_id = uuid4()
        data = {
            "id": user_id,
            "username": "testuser",
            "email": "test@example.com",
            "role": UserRole.PLAYER,
            "status": UserStatus.ACTIVE,
            "is_verified": True,
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "max_characters": 5,
        }

        response = UserResponse(**data)

        assert response.id == user_id
        assert response.username == "testuser"
        assert response.email == "test@example.com"
        assert response.role == UserRole.PLAYER
        assert response.status == UserStatus.ACTIVE
        assert response.is_verified is True
        assert response.max_characters == 5


class TestUserSessionResponse:
    """Test user session response schema."""

    def test_session_response_creation(self):
        """Test creating session response from data."""
        session_id = uuid4()
        now = datetime.now()

        data = {
            "id": session_id,
            "device_info": "iPhone 12",
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0...",
            "is_active": True,
            "created_at": now,
            "expires_at": now,
            "last_activity": now,
        }

        response = UserSessionResponse(**data)

        assert response.id == session_id
        assert response.device_info == "iPhone 12"
        assert response.ip_address == "192.168.1.1"
        assert response.user_agent == "Mozilla/5.0..."
        assert response.is_active is True


class TestLogoutRequest:
    """Test logout request schema."""

    def test_logout_request_default(self):
        """Test logout request with default values."""
        request = LogoutRequest()

        assert request.revoke_all_sessions is False

    def test_logout_request_revoke_all(self):
        """Test logout request with revoke all sessions."""
        data = {"revoke_all_sessions": True}

        request = LogoutRequest(**data)

        assert request.revoke_all_sessions is True


class TestAuthenticationResponse:
    """Test authentication response schema."""

    def test_authentication_response_success(self):
        """Test successful authentication response."""
        user_data = {
            "id": uuid4(),
            "username": "testuser",
            "email": "test@example.com",
            "role": UserRole.PLAYER,
            "status": UserStatus.ACTIVE,
            "is_verified": True,
            "created_at": datetime.now(),
            "last_login": datetime.now(),
            "max_characters": 5,
        }

        token_data = {
            "access_token": "access_token_here",
            "refresh_token": "refresh_token_here",
            "expires_in": 900,
        }

        data = {
            "message": "Login successful",
            "success": True,
            "user": UserResponse(**user_data),
            "tokens": TokenResponse(**token_data),
        }

        response = AuthenticationResponse(**data)

        assert response.message == "Login successful"
        assert response.success is True
        assert response.user is not None
        assert response.tokens is not None

    def test_authentication_response_failure(self):
        """Test failed authentication response."""
        data = {"message": "Authentication failed", "success": False}

        response = AuthenticationResponse(**data)

        assert response.message == "Authentication failed"
        assert response.success is False
        assert response.user is None
        assert response.tokens is None


class TestErrorResponse:
    """Test error response schema."""

    def test_error_response_simple(self):
        """Test simple error response."""
        data = {"message": "Something went wrong"}

        response = ErrorResponse(**data)

        assert response.message == "Something went wrong"
        assert response.error_code is None
        assert response.details is None

    def test_error_response_detailed(self):
        """Test detailed error response."""
        data = {
            "message": "Validation error",
            "error_code": "VALIDATION_FAILED",
            "details": {"field": "username", "reason": "Already exists"},
        }

        response = ErrorResponse(**data)

        assert response.message == "Validation error"
        assert response.error_code == "VALIDATION_FAILED"
        assert response.details["field"] == "username"
        assert response.details["reason"] == "Already exists"
