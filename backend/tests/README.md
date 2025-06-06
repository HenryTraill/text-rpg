# Test Suite Documentation

This directory contains the comprehensive test suite for the Text RPG API Gateway and Authentication System. The test suite covers all major functionality implemented in GitHub Issue #5.

## 📋 Test Coverage

The test suite covers the following components:

### 🔐 Authentication System
- JWT token creation and validation
- Password hashing and verification
- User authentication and session management
- Token refresh mechanism
- Session tracking and revocation

### 🛡️ Security & Middleware
- Rate limiting with Redis backend
- Security headers and CORS protection
- Request validation and sanitization
- Input validation with Pydantic schemas
- IP filtering and security event logging

### 🏥 Health Monitoring
- Database connectivity checks
- Redis connectivity monitoring
- System resource monitoring
- Health status aggregation
- Readiness and liveness probes

### 🌐 API Endpoints
- User registration and login
- Profile management
- Session management
- Password changes
- Health check endpoints

## 🗂️ Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # Unit tests (isolated components)
│   ├── test_auth_utils.py      # Authentication utilities
│   ├── test_auth_schemas.py    # Pydantic schema validation
│   └── test_health.py          # Health check system
├── middleware/                 # Middleware tests
│   ├── test_rate_limit.py      # Rate limiting middleware
│   └── test_security.py        # Security middleware
├── integration/                # Integration tests (multiple components)
│   ├── test_auth_endpoints.py  # Authentication API endpoints
│   └── test_health_endpoints.py # Health check endpoints
└── README.md                   # This file
```

## 🚀 Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run with coverage report
python run_tests.py --coverage

# Check if test dependencies are installed
python run_tests.py --check-deps
```

### Test Categories

```bash
# Unit tests only
python run_tests.py --unit

# Integration tests only  
python run_tests.py --integration

# Middleware tests only
python run_tests.py --middleware

# Authentication tests only
python run_tests.py --auth

# Health check tests only
python run_tests.py --health

# Fast tests (excluding slow ones)
python run_tests.py --fast
```

### Specific Test Files

```bash
# Run a specific test file
python run_tests.py --file tests/unit/test_auth_utils.py

# Run tests matching a pattern
pytest -k "test_password" -v

# Run a specific test method
pytest tests/unit/test_auth_utils.py::TestAuthUtils::test_password_hashing -v
```

### Using pytest directly

```bash
# Basic test run
pytest

# With coverage
pytest --cov=app --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto
```

## 📊 Coverage Reports

The test suite generates coverage reports in multiple formats:

- **Terminal**: Shows coverage summary in the terminal
- **HTML**: Detailed coverage report at `htmlcov/index.html`
- **XML**: Machine-readable coverage data at `coverage.xml`

```bash
# Generate and open HTML coverage report
python run_tests.py --coverage
```

## 🏷️ Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.middleware` - Middleware tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.health` - Health check tests
- `@pytest.mark.slow` - Slow-running tests

```bash
# Run tests by marker
pytest -m "unit and auth"
pytest -m "not slow"
```

## 🛠️ Test Configuration

### Environment Variables

Tests automatically set up a test environment with:

```bash
ENVIRONMENT=test
DATABASE_URL=sqlite:///test.db
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=test-secret-key-for-testing-only
API_RATE_LIMIT=1000
```

### pytest.ini

The `pytest.ini` file configures:
- Test discovery patterns
- Coverage settings (80% minimum)
- Warning filters
- Output formatting

### conftest.py

Provides shared fixtures:
- Mock database sessions
- Mock Redis clients
- Sample users and test data
- Authentication helpers
- Request/response mocks

## 📝 Writing Tests

### Test Structure

Follow this structure for new tests:

```python
"""
Test module docstring describing what is being tested.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.module_under_test import ComponentUnderTest


class TestComponentUnderTest:
    """Test suite for ComponentUnderTest."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return {"key": "value"}
    
    def test_basic_functionality(self, sample_data):
        """Test basic functionality with descriptive name."""
        # Arrange
        component = ComponentUnderTest()
        
        # Act
        result = component.do_something(sample_data)
        
        # Assert
        assert result is not None
        assert result["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        # Use AsyncMock for async dependencies
        with patch('app.module.dependency', new_callable=AsyncMock) as mock_dep:
            mock_dep.return_value = "mocked_result"
            
            component = ComponentUnderTest()
            result = await component.async_method()
            
            assert result == "mocked_result"
            mock_dep.assert_called_once()
```

### Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies** (database, Redis, HTTP calls)
4. **Test both success and failure cases**
5. **Use fixtures for common test data**
6. **Add appropriate markers** for test categorization
7. **Keep tests isolated** - each test should be independent
8. **Test edge cases** and error conditions

### Mock Guidelines

```python
# Mock external dependencies
@patch('app.core.database.get_session')
def test_with_db_mock(mock_get_session):
    mock_session = Mock()
    mock_get_session.return_value = mock_session
    # Test implementation

# Mock async functions
@patch('app.core.auth.auth_utils.authenticate_user', new_callable=AsyncMock)
async def test_async_mock(mock_auth):
    mock_auth.return_value = sample_user
    # Test implementation

# Mock Redis
@patch('redis.from_url')
def test_with_redis_mock(mock_redis):
    mock_client = Mock()
    mock_redis.return_value = mock_client
    # Test implementation
```

## 🔧 Dependencies

Required packages for testing:

```bash
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
fastapi[all]>=0.100.0
```

Install with:
```bash
pip install pytest pytest-cov pytest-asyncio httpx fastapi[all]
```

## 📈 Test Metrics

Current test coverage targets:
- **Overall**: 80% minimum
- **Authentication**: 90% minimum  
- **Security**: 85% minimum
- **Health checks**: 90% minimum

## 🐛 Debugging Tests

### Common Issues

1. **Import errors**: Ensure `PYTHONPATH` includes the app directory
2. **Database errors**: Tests use mocked database by default
3. **Redis errors**: Tests use mocked Redis by default
4. **JWT errors**: Tests use test-specific secret keys

### Debugging Commands

```bash
# Run with debugging output
pytest -v -s

# Run with pdb on failure
pytest --pdb

# Show local variables on failure
pytest -l

# Run a single test with maximum verbosity
pytest tests/unit/test_auth_utils.py::TestAuthUtils::test_password_hashing -vvs
```

### VS Code Integration

Add to `.vscode/settings.json`:

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.cwd": "${workspaceFolder}/backend"
}
```

## 🔄 Continuous Integration

Tests are designed to run in CI environments:

- **GitHub Actions**: Configured in `.github/workflows/`
- **Environment**: Uses environment variables for configuration
- **Databases**: Uses SQLite for CI, PostgreSQL for local development
- **Redis**: Uses mocked Redis client in tests

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

For questions about the test suite, refer to the project documentation or open an issue in the repository. 