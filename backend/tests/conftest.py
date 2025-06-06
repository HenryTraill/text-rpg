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
def authenticated_client(sample_user):
    """Create a test client with authentication dependency overridden."""
    from app.routers.auth import get_current_user
    from app.core.database import get_session
    
    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: sample_user
    app.dependency_overrides[get_session] = lambda: AsyncMock()
    
    client = TestClient(app)
    
    yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def override_get_current_user():
    """Helper fixture to override get_current_user dependency."""
    from app.routers.auth import get_current_user
    
    def _override_user(user):
        app.dependency_overrides[get_current_user] = lambda: user
        return lambda: None  # Return cleanup function
    
    yield _override_user
    
    # Clean up
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


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
def db_session():
    """Create a database session fixture with realistic mock behavior."""
    from sqlalchemy.exc import IntegrityError
    from app.core.database import get_session
    import uuid
    
    # Storage for mocked data - simulates database persistence
    mock_storage = {
        'users': [],
        'skills': [],
        'zones': [],
        'locations': [],
        'items': [],
        'characters': [],
        'chat_channels': [],
        'npc_merchants': [],
        'user_sessions': [],
        'trades': [],
        'guilds': [],
        'combat_sessions': [],
        'inventory_slots': [],
        'character_skills': []
    }
    
    # Track objects pending commit for constraint checking
    pending_objects = []
    
    def mock_add(obj):
        """Mock add that queues objects for commit."""
        obj_type = type(obj).__name__.lower()
        
        # Generate ID if not present and model has an id field
        if hasattr(obj, 'id') and obj.id is None:
            obj.id = uuid.uuid4()
        
        # Add to pending list for constraint checking during commit
        pending_objects.append(obj)
    
    async def mock_commit():
        """Mock commit that validates constraints and persists objects."""
        for obj in pending_objects:
            obj_type = type(obj).__name__.lower()
            
            # Check for unique constraints before committing
            if obj_type == 'user':
                # Check username/email uniqueness
                for existing in mock_storage.get('users', []):
                    if (hasattr(existing, 'username') and hasattr(obj, 'username') and 
                        existing.username == obj.username):
                        raise IntegrityError("Duplicate username", None, None)
                    if (hasattr(existing, 'email') and hasattr(obj, 'email') and 
                        existing.email == obj.email):
                        raise IntegrityError("Duplicate email", None, None)
            elif obj_type == 'skill':
                # Check skill name uniqueness
                for existing in mock_storage.get('skills', []):
                    if (hasattr(existing, 'name') and hasattr(obj, 'name') and 
                        existing.name == obj.name):
                        raise IntegrityError("Duplicate skill name", None, None)
            elif obj_type == 'character':
                # Check character name uniqueness
                for existing in mock_storage.get('characters', []):
                    if (hasattr(existing, 'name') and hasattr(obj, 'name') and 
                        existing.name == obj.name):
                        raise IntegrityError("Duplicate character name", None, None)
            elif obj_type == 'zone':
                # Check zone name uniqueness
                for existing in mock_storage.get('zones', []):
                    if (hasattr(existing, 'name') and hasattr(obj, 'name') and 
                        existing.name == obj.name):
                        raise IntegrityError("Duplicate zone name", None, None)
            
            # Store the object with correct table name mapping
            table_mapping = {
                'chatchannel': 'chat_channels',
                'npcmerchant': 'npc_merchants',
                'characterskill': 'character_skills',
                'usersession': 'user_sessions',
                'inventoryslot': 'inventory_slots',
                'combatsession': 'combat_sessions'
            }
            
            table_name = table_mapping.get(obj_type, f"{obj_type}s")
            if table_name not in mock_storage:
                mock_storage[table_name] = []
            mock_storage[table_name].append(obj)
        
        # Clear pending objects after successful commit
        pending_objects.clear()
    
    def mock_add_all(objects):
        """Mock add_all that adds multiple objects."""
        for obj in objects:
            mock_add(obj)
    
    async def mock_execute(statement):
        """Mock execute that simulates SELECT queries with sophisticated WHERE clause parsing."""
        import re
        
        # Try to get compiled SQL with actual parameter values
        statement_str = str(statement).lower()
        compiled_sql = statement_str
        
        try:
            # Attempt to get compiled SQL with bound parameters
            if hasattr(statement, 'compile'):
                compiled = statement.compile(compile_kwargs={"literal_binds": True})
                compiled_sql = str(compiled).lower()
        except:
            # Fallback to original parsing if compilation fails
            pass
        
        mock_result = Mock()
        
        # Simulate different query patterns
        if 'select' in statement_str:
            results = []
            
            # Determine the primary table
            table_name = None
            if 'from skills' in statement_str or 'skills.' in statement_str:
                table_name = 'skills'
                results = mock_storage.get('skills', [])
            elif 'from items' in statement_str or 'items.' in statement_str:
                table_name = 'items'
                results = mock_storage.get('items', [])
            elif 'from users' in statement_str or 'users.' in statement_str:
                table_name = 'users'
                results = mock_storage.get('users', [])
            elif 'from characters' in statement_str or 'characters.' in statement_str:
                table_name = 'characters'
                results = mock_storage.get('characters', [])
            elif 'from zones' in statement_str or 'zones.' in statement_str:
                table_name = 'zones'
                results = mock_storage.get('zones', [])
            elif 'from locations' in statement_str or 'locations.' in statement_str:
                table_name = 'locations'
                results = mock_storage.get('locations', [])
            elif 'from chat_channels' in statement_str or 'chat_channels.' in statement_str:
                table_name = 'chat_channels'
                results = mock_storage.get('chat_channels', [])
            elif 'from npc_merchants' in statement_str or 'npc_merchants.' in statement_str:
                table_name = 'npc_merchants'
                results = mock_storage.get('npc_merchants', [])
            
            # Apply sophisticated WHERE clause filtering
            if table_name and 'where' in statement_str:
                results = apply_where_filters(results, compiled_sql, table_name)
                
            # Handle non-WHERE specific patterns for backwards compatibility
            elif table_name == 'locations' and 'general store' in statement_str:
                results = [l for l in results if hasattr(l, 'name') and 'general store' in l.name.lower()]
                
            # Handle JOIN queries
            elif any(table in statement_str for table in ['join', 'users', 'characters']):
                if 'characters' in statement_str:
                    results = mock_storage.get('characters', [])
                elif 'users' in statement_str:
                    results = mock_storage.get('users', [])
            
            # Setup mock result methods
            mock_result.scalars.return_value.all.return_value = results
            mock_result.scalars.return_value.first.return_value = results[0] if results else None
            mock_result.scalar_one_or_none.return_value = results[0] if results else None
            mock_result.scalar_one.return_value = results[0] if results else None
            
        else:
            # For non-SELECT statements
            mock_result.scalars.return_value.all.return_value = []
            mock_result.scalars.return_value.first.return_value = None
            mock_result.scalar_one_or_none.return_value = None
        
        return mock_result
    
    def apply_where_filters(results, sql_str, table_name):
        """Apply WHERE clause filters to mock data."""
        import re
        
        # Extract WHERE clause
        where_match = re.search(r'where\s+(.+?)(?:\s+order\s+by|\s+group\s+by|\s+limit|\s*$)', sql_str, re.IGNORECASE | re.DOTALL)
        if not where_match:
            return results
            
        where_clause = where_match.group(1).strip()
        

        
        # Handle skills table filters
        if table_name == 'skills':
            # Look for category filter: skills.category = 'combat' or similar
            category_match = re.search(r"skills\.category\s*=\s*['\"]?(\w+)['\"]?", where_clause)
            if category_match:
                category_value = category_match.group(1).lower()
                # Use .value to get the enum's string value, not its representation
                results = [s for s in results if hasattr(s, 'category') and 
                          (s.category.value if hasattr(s.category, 'value') else str(s.category)).lower() == category_value]
            
            # Look for name exact match: skills.name = 'Swordsmanship' (case-insensitive)
            name_match = re.search(r"skills\.name\s*=\s*['\"]([^'\"]+)['\"]", where_clause)
            if name_match:
                name_value = name_match.group(1)
                results = [s for s in results if hasattr(s, 'name') and s.name.lower() == name_value.lower()]
            
            # Look for LIKE pattern: skills.name LIKE '%uuid%'  
            like_match = re.search(r"skills\.name\s+like\s+['\"]%([a-f0-9\-]{6,})[a-f0-9\-]*%['\"]", where_clause)
            if like_match:
                uuid_pattern = like_match.group(1)
                results = [s for s in results if hasattr(s, 'name') and uuid_pattern in s.name.lower()]
                
        # Handle items table filters
        elif table_name == 'items':
            # Look for item_type filter: items.item_type = 'weapon' or similar
            type_match = re.search(r"items\.item_type\s*=\s*['\"]?(\w+)['\"]?", where_clause)
            if type_match:
                type_value = type_match.group(1).lower()
                results = [i for i in results if hasattr(i, 'item_type') and str(i.item_type).lower() == type_value]
            
            # Look for LIKE pattern: items.name LIKE '%uuid%'
            like_match = re.search(r"items\.name\s+like\s+['\"]%([a-f0-9\-]{6,})[a-f0-9\-]*%['\"]", where_clause)
            if like_match:
                uuid_pattern = like_match.group(1)
                results = [i for i in results if hasattr(i, 'name') and uuid_pattern in i.name.lower()]
        
        return results
    
    # Create mock session with realistic behavior
    mock_session = AsyncMock()
    mock_session.add = Mock(side_effect=mock_add)
    mock_session.add_all = Mock(side_effect=mock_add_all)
    mock_session.commit = AsyncMock(side_effect=mock_commit)
    mock_session.refresh = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=mock_execute)
    mock_session.rollback = AsyncMock()
    
    return mock_session


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
    from app.core.database import get_session
    
    # Create mock session with async methods
    mock_session = AsyncMock()
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.exec = Mock()  # For backward compatibility
    mock_session.rollback = AsyncMock()
    
    # Mock result objects
    mock_result = Mock()
    mock_result.scalars.return_value.first.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_result.fetchone.return_value = None
    mock_result.scalar.return_value = None
    mock_session.execute.return_value = mock_result
    mock_session.exec.return_value = mock_result
    
    # Override FastAPI dependency
    app.dependency_overrides[get_session] = lambda: mock_session
    
    with (
        patch("app.core.database.get_engine") as mock_get_engine,
    ):
        # Mock engine
        mock_engine = Mock()
        mock_get_engine.return_value = mock_engine

        yield {"session": mock_session, "engine": mock_engine}
    
    # Clean up dependency overrides
    if get_session in app.dependency_overrides:
        del app.dependency_overrides[get_session]


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


# Model factories for testing
def UserFactory(**overrides):
    """Create test user data."""
    from app.models.user import UserRole, UserStatus
    data = {
        "username": f"testuser_{uuid4().hex[:8]}",
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "hashed_password": auth_utils.get_password_hash("TestPassword123!"),
        "role": UserRole.PLAYER,
        "status": UserStatus.ACTIVE,
        "is_verified": True,
        "max_characters": 5,
        "chat_settings": {"global_enabled": True, "private_enabled": True},
        "privacy_settings": {"show_online_status": True, "allow_friend_requests": True},
    }
    data.update(overrides)
    return data


def SkillFactory(**overrides):
    """Create test skill data."""
    from app.models.skill import SkillCategory
    data = {
        "name": f"Test Skill {uuid4().hex[:8]}",
        "description": "A test skill for testing purposes",
        "category": SkillCategory.COMBAT.value,
        "max_level": 100,
        "base_experience": 100,
        "experience_multiplier": 1.5,
        "stat_bonuses": {"strength": 1, "agility": 1},
        "abilities": {"basic_attack": {"level": 1, "damage": 10}},
        "prerequisite_skills": {},
        "is_active": True,
    }
    data.update(overrides)
    return data


def ZoneFactory(**overrides):
    """Create test zone data."""
    data = {
        "name": f"Test Zone {uuid4().hex[:8]}",
        "description": "A test zone for testing purposes",
        "min_x": 0.0,
        "max_x": 1000.0,
        "min_y": 0.0,
        "max_y": 1000.0,
        "level_requirement": 1,
        "is_safe": True,
        "is_active": True,
        "spawn_rates": {"monster": 0.1, "resource": 0.2},
        "weather_effects": {"clear": 0.7, "rain": 0.3},
        "special_properties": {},
    }
    data.update(overrides)
    return data


def ItemFactory(**overrides):
    """Create test item data."""
    from app.models.inventory import ItemType, ItemRarity
    data = {
        "name": f"Test Item {uuid4().hex[:8]}",
        "description": "A test item for testing purposes",
        "item_type": ItemType.WEAPON.value,
        "rarity": ItemRarity.COMMON.value,
        "base_value": 100,
        "weight": 1.0,
        "max_stack": 1,
        "is_tradeable": True,
        "is_consumable": False,
        "stats": {"damage": 10, "accuracy": 5},
        "effects": {},
        "attributes": {},
    }
    data.update(overrides)
    return data


def CharacterFactory(**overrides):
    """Create test character data."""
    data = {
        "name": f"TestChar_{uuid4().hex[:8]}",
        "class_type": "warrior",
        "level": 1,
        "experience": 0,
        "health": 100,
        "max_health": 100,
        "mana": 50,
        "max_mana": 50,
        "strength": 10,
        "agility": 10,
        "intelligence": 10,
        "vitality": 10,
        "luck": 10,
        "gold": 100,
        "x_coordinate": 500.0,
        "y_coordinate": 500.0,
        "is_online": False,
        "is_active": True,
        "last_login": None,
        "stats": {},
        "preferences": {},
    }
    data.update(overrides)
    return data
