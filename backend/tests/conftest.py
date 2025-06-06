"""
Pytest configuration and shared fixtures for the test suite.

Provides common test fixtures and configuration for:
- Database testing setup
- Authentication mocking
- Test client configuration
- Environment setup
"""

import pytest
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone
from uuid import uuid4
from fastapi.testclient import TestClient

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.core.auth import auth_utils
from app.models.user import User, UserRole, UserStatus


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"
    os.environ["REDIS_URL"] = "redis://localhost:6379/1"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["API_RATE_LIMIT"] = "1000"  # Higher limit for testing


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.exec = Mock()
    return session


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = Mock()
    client.get = Mock()
    client.set = Mock()
    client.delete = Mock()
    client.exists = Mock()
    client.ping = Mock(return_value=True)
    client.info = Mock(return_value={"redis_version": "6.2.0"})
    return client


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password=auth_utils.get_password_hash("TestPassword123!"),
        role=UserRole.PLAYER,
        status=UserStatus.ACTIVE,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login=None,
        max_characters=5,
        chat_settings={},
        privacy_settings={},
    )


@pytest.fixture
def admin_user():
    """Create an admin user for testing."""
    return User(
        id=uuid4(),
        username="admin",
        email="admin@example.com",
        hashed_password=auth_utils.get_password_hash("AdminPassword123!"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login=None,
        max_characters=10,
        chat_settings={},
        privacy_settings={},
    )


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6OTk5OTk5OTk5OX0.test"


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Create authentication headers for testing."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture
def mock_auth_utils():
    """Create a mock auth utils instance."""
    with patch("app.core.auth.auth_utils") as mock:
        mock.get_password_hash = Mock(return_value="hashed_password")
        mock.verify_password = Mock(return_value=True)
        mock.create_access_token = Mock(return_value="access_token")
        mock.create_refresh_token = Mock(return_value="refresh_token")
        mock.verify_token = Mock(return_value={"sub": "testuser", "jti": "token_jti"})
        mock.authenticate_user = AsyncMock()
        mock.get_user_by_username = AsyncMock()
        mock.get_user_by_email = AsyncMock()
        mock.get_user_by_id = AsyncMock()
        mock.create_user_session = AsyncMock()
        mock.revoke_user_session = AsyncMock()
        mock.is_token_revoked = AsyncMock(return_value=False)
        yield mock


@pytest.fixture
def mock_get_current_user(sample_user):
    """Mock the get_current_user dependency."""
    with patch("app.routers.auth.get_current_user", return_value=sample_user) as mock:
        yield mock


@pytest.fixture
def mock_rate_limiter():
    """Mock the rate limiting middleware."""
    with patch("app.middleware.rate_limit.RateLimitMiddleware") as mock:
        mock_instance = Mock()
        mock_instance.dispatch = AsyncMock(
            side_effect=lambda request, call_next: call_next(request)
        )
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_security_middleware():
    """Mock the security middleware."""
    with patch("app.middleware.security.SecurityMiddleware") as mock:
        mock_instance = Mock()
        mock_instance.dispatch = AsyncMock(
            side_effect=lambda request, call_next: call_next(request)
        )
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_health_checker():
    """Mock the health checker."""
    with patch("app.core.health.health_checker") as mock:
        mock.get_health_status = AsyncMock(
            return_value={
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "uptime": 3600,
                "version": "1.0.0",
                "checks": {
                    "database": {"status": "healthy"},
                    "redis": {"status": "healthy"},
                    "system": {"status": "healthy"},
                },
            }
        )
        mock.is_ready = AsyncMock(return_value=True)
        mock.is_alive = AsyncMock(return_value=True)
        yield mock


@pytest.fixture(autouse=True)
def mock_database_dependencies():
    """Automatically mock database dependencies for all tests."""
    with patch("app.core.database.get_session") as mock_get_session, patch(
        "app.core.database.get_engine"
    ) as mock_get_engine:

        # Mock session
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        mock_session.exec = Mock()
        mock_get_session.return_value = mock_session

        # Mock engine
        mock_engine = Mock()
        mock_get_engine.return_value = mock_engine

        yield {"session": mock_session, "engine": mock_engine}


@pytest.fixture(autouse=True)
def mock_redis_dependencies():
    """Automatically mock Redis dependencies for all tests."""
    with patch("redis.from_url") as mock_redis_factory:
        mock_client = Mock()
        mock_client.ping = Mock(return_value=True)
        mock_client.get = Mock()
        mock_client.set = Mock()
        mock_client.delete = Mock()
        mock_client.exists = Mock()
        mock_client.pipeline = Mock()
        mock_redis_factory.return_value = mock_client
        yield mock_client


@pytest.fixture
def disable_auth():
    """Disable authentication for testing endpoints without auth."""
    with patch("app.routers.auth.get_current_user") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request object."""
    request = Mock()
    request.method = "GET"
    request.url.path = "/test"
    request.headers = {}
    request.client.host = "127.0.0.1"
    request.url.__str__ = Mock(return_value="http://localhost:8000/test")
    return request


@pytest.fixture
def mock_response():
    """Create a mock FastAPI response object."""
    from starlette.responses import Response

    return Response("OK", status_code=200)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "middleware: mark test as middleware test")
    config.addinivalue_line("markers", "auth: mark test as authentication test")
    config.addinivalue_line("markers", "health: mark test as health check test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Automatically add markers based on test file location."""
    for item in items:
        # Add markers based on file path
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "middleware" in str(item.fspath):
            item.add_marker(pytest.mark.middleware)

        # Add markers based on test name patterns
        if "auth" in item.name.lower():
            item.add_marker(pytest.mark.auth)
        elif "health" in item.name.lower():
            item.add_marker(pytest.mark.health)


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def user_registration_data(**overrides):
        """Create user registration data."""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword123!",
            "password_confirm": "TestPassword123!",
        }
        data.update(overrides)
        return data

    @staticmethod
    def user_login_data(**overrides):
        """Create user login data."""
        data = {"username": "testuser", "password": "TestPassword123!"}
        data.update(overrides)
        return data

    @staticmethod
    def password_change_data(**overrides):
        """Create password change data."""
        data = {
            "current_password": "CurrentPassword123!",
            "new_password": "NewPassword123!",
            "new_password_confirm": "NewPassword123!",
        }
        data.update(overrides)
        return data


@pytest.fixture
def test_data():
    """Provide test data factory."""
    return TestDataFactory
