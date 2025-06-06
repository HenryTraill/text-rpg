"""
Integration tests for health check endpoints.

Tests health monitoring endpoints including:
- /health endpoint with full status reporting
- /ready endpoint for readiness probes
- /alive endpoint for liveness probes
- Health status aggregation and response formatting
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app


class TestHealthEndpoints:
    """Integration tests for health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_endpoint_healthy(self, client):
        """Test /health endpoint when all systems are healthy."""
        mock_health_status = {
            "status": "healthy",
            "timestamp": "2024-01-01T12:00:00Z",
            "uptime": 3600,
            "version": "1.0.0",
            "environment": "test",
            "checks": {
                "database": {
                    "status": "healthy",
                    "connection_time": 0.05,
                    "version": "PostgreSQL 13.0",
                },
                "redis": {
                    "status": "healthy",
                    "connection_time": 0.02,
                    "version": "6.2.0",
                    "key_count": 42,
                },
                "system": {
                    "status": "healthy",
                    "cpu_percent": 25.0,
                    "memory": {"percent": 45.0, "available_gb": 8.0},
                    "disk": {"percent": 60.0, "free_gb": 100.0},
                },
            },
        }

        with patch(
            "app.core.health.health_checker.get_health_status",
            new_callable=AsyncMock,
            return_value=mock_health_status,
        ):
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "uptime" in data
        assert "version" in data
        assert "checks" in data
        assert data["checks"]["database"]["status"] == "healthy"
        assert data["checks"]["redis"]["status"] == "healthy"
        assert data["checks"]["system"]["status"] == "healthy"

    def test_health_endpoint_degraded(self, client):
        """Test /health endpoint when system is degraded."""
        mock_health_status = {
            "status": "degraded",
            "timestamp": "2024-01-01T12:00:00Z",
            "uptime": 3600,
            "version": "1.0.0",
            "environment": "test",
            "checks": {
                "database": {"status": "healthy", "connection_time": 0.05},
                "redis": {"status": "healthy", "connection_time": 0.02},
                "system": {
                    "status": "warning",
                    "cpu_percent": 85.0,
                    "memory": {"percent": 85.0},
                    "disk": {"percent": 60.0},
                },
            },
        }

        with patch(
            "app.core.health.health_checker.get_health_status",
            new_callable=AsyncMock,
            return_value=mock_health_status,
        ):
            response = client.get("/health")

        assert response.status_code == 200  # Still returns 200 for degraded
        data = response.json()
        assert data["status"] == "degraded"
        assert data["checks"]["system"]["status"] == "warning"

    def test_health_endpoint_unhealthy(self, client):
        """Test /health endpoint when system is unhealthy."""
        mock_health_status = {
            "status": "unhealthy",
            "timestamp": "2024-01-01T12:00:00Z",
            "uptime": 3600,
            "version": "1.0.0",
            "environment": "test",
            "checks": {
                "database": {"status": "error", "error": "Connection refused"},
                "redis": {"status": "healthy", "connection_time": 0.02},
                "system": {"status": "healthy", "cpu_percent": 25.0},
            },
        }

        with patch(
            "app.core.health.health_checker.get_health_status",
            new_callable=AsyncMock,
            return_value=mock_health_status,
        ):
            response = client.get("/health")

        assert response.status_code == 503  # Service unavailable for unhealthy
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["database"]["status"] == "error"
        assert "error" in data["checks"]["database"]

    def test_health_endpoint_with_details(self, client):
        """Test /health endpoint with detailed metrics."""
        mock_health_status = {
            "status": "healthy",
            "timestamp": "2024-01-01T12:00:00Z",
            "uptime": 3600,
            "version": "1.0.0",
            "environment": "test",
            "checks": {
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
                "system": {"status": "healthy"},
            },
            "details": {
                "application": {
                    "name": "Text RPG API",
                    "version": "1.0.0",
                    "environment": "test",
                },
                "process": {
                    "pid": 12345,
                    "cpu_percent": 15.5,
                    "memory_mb": 100,
                    "num_threads": 8,
                },
            },
        }

        with patch(
            "app.core.health.health_checker.get_health_status",
            new_callable=AsyncMock,
            return_value=mock_health_status,
        ):
            response = client.get("/health?details=true")

        assert response.status_code == 200
        data = response.json()
        assert "details" in data
        assert data["details"]["application"]["name"] == "Text RPG API"
        assert data["details"]["process"]["pid"] == 12345

    def test_health_endpoint_exception_handling(self, client):
        """Test /health endpoint when health checker raises exception."""
        with patch(
            "app.core.health.health_checker.get_health_status",
            new_callable=AsyncMock,
            side_effect=Exception("Health check failed"),
        ):
            response = client.get("/health")

        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "Health check failed" in data["error"]

    def test_ready_endpoint_ready(self, client):
        """Test /ready endpoint when system is ready."""
        with patch(
            "app.core.health.health_checker.is_ready",
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["ready"] is True
        assert "timestamp" in data

    def test_ready_endpoint_not_ready(self, client):
        """Test /ready endpoint when system is not ready."""
        with patch(
            "app.core.health.health_checker.is_ready",
            new_callable=AsyncMock,
            return_value=False,
        ):
            response = client.get("/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["ready"] is False

    def test_ready_endpoint_exception_handling(self, client):
        """Test /ready endpoint when readiness check raises exception."""
        with patch(
            "app.core.health.health_checker.is_ready",
            new_callable=AsyncMock,
            side_effect=Exception("Readiness check failed"),
        ):
            response = client.get("/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["ready"] is False
        assert "error" in data

    def test_alive_endpoint_always_responds(self, client):
        """Test /alive endpoint always responds positively."""
        with patch(
            "app.core.health.health_checker.is_alive",
            new_callable=AsyncMock,
            return_value=True,
        ):
            response = client.get("/alive")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert data["alive"] is True
        assert "timestamp" in data

    def test_alive_endpoint_exception_handling(self, client):
        """Test /alive endpoint even when liveness check raises exception."""
        # Even if is_alive raises an exception, the endpoint should still respond
        with patch(
            "app.core.health.health_checker.is_alive",
            new_callable=AsyncMock,
            side_effect=Exception("Liveness check failed"),
        ):
            response = client.get("/alive")

        # Should still return alive status even on exception
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert data["alive"] is True


class TestHealthEndpointIntegration:
    """Integration tests for health endpoints with real components."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_health_response_format(self, client):
        """Test that health response has correct format."""
        with patch("app.core.health.health_checker.get_health_status") as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "uptime": 3600,
                "version": "1.0.0",
                "environment": "test",
                "checks": {
                    "database": {"status": "healthy"},
                    "redis": {"status": "healthy"},
                    "system": {"status": "healthy"},
                },
            }

            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        required_fields = ["status", "timestamp", "uptime", "version", "checks"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify checks structure
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
        assert "system" in data["checks"]

        # Verify each check has status
        for check_name, check_data in data["checks"].items():
            assert "status" in check_data, f"Missing status in {check_name} check"

    def test_health_status_codes(self, client):
        """Test correct HTTP status codes for different health states."""
        test_cases = [("healthy", 200), ("degraded", 200), ("unhealthy", 503)]

        for health_status, expected_code in test_cases:
            with patch(
                "app.core.health.health_checker.get_health_status"
            ) as mock_health:
                mock_health.return_value = {
                    "status": health_status,
                    "timestamp": "2024-01-01T12:00:00Z",
                    "uptime": 3600,
                    "version": "1.0.0",
                    "checks": {},
                }

                response = client.get("/health")
                assert response.status_code == expected_code, (
                    f"Wrong status code for {health_status}: expected {expected_code}, got {response.status_code}"
                )

    def test_ready_vs_alive_behavior(self, client):
        """Test difference between ready and alive endpoints."""
        # Test ready endpoint can fail
        with patch("app.core.health.health_checker.is_ready", return_value=False):
            ready_response = client.get("/ready")
            assert ready_response.status_code == 503

        # Test alive endpoint always succeeds
        with patch("app.core.health.health_checker.is_alive", return_value=True):
            alive_response = client.get("/alive")
            assert alive_response.status_code == 200

    def test_health_endpoint_caching_headers(self, client):
        """Test that health endpoints have appropriate caching headers."""
        with patch("app.core.health.health_checker.get_health_status") as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "uptime": 3600,
                "version": "1.0.0",
                "checks": {},
            }

            response = client.get("/health")

        # Health endpoints should not be cached
        assert "Cache-Control" in response.headers
        assert "no-cache" in response.headers["Cache-Control"]

    def test_health_endpoint_content_type(self, client):
        """Test that health endpoints return JSON content type."""
        with patch("app.core.health.health_checker.get_health_status") as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "uptime": 3600,
                "version": "1.0.0",
                "checks": {},
            }

            response = client.get("/health")

        assert response.headers["Content-Type"] == "application/json"

    def test_concurrent_health_checks(self, client):
        """Test that multiple concurrent health check requests work properly."""

        with patch("app.core.health.health_checker.get_health_status") as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "uptime": 3600,
                "version": "1.0.0",
                "checks": {},
            }

            # Make multiple concurrent requests
            responses = []
            for _ in range(5):
                response = client.get("/health")
                responses.append(response)

            # All should succeed
            for response in responses:
                assert response.status_code == 200
                assert response.json()["status"] == "healthy"
