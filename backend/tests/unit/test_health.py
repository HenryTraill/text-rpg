"""
Unit tests for health check system.

Tests comprehensive health monitoring including:
- Database connectivity checks
- Redis connectivity checks
- System resource monitoring
- Health status aggregation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.core.health import HealthChecker, health_checker


class TestHealthChecker:
    """Test suite for HealthChecker class."""

    @pytest.fixture
    def mock_health_checker(self):
        """Create a health checker with mocked dependencies."""
        with patch("app.core.health.redis") as mock_redis:
            mock_redis.from_url.return_value = Mock()
            checker = HealthChecker()
            return checker

    @pytest.mark.asyncio
    async def test_get_health_status_healthy(self, mock_health_checker):
        """Test health status when all components are healthy."""
        # Mock all check methods to return healthy status
        mock_health_checker._check_database = AsyncMock(
            return_value={"status": "healthy", "connection_time": 0.1}
        )
        mock_health_checker._check_redis = AsyncMock(
            return_value={"status": "healthy", "connection_time": 0.05}
        )
        mock_health_checker._check_system_resources = AsyncMock(
            return_value={"status": "healthy", "cpu_percent": 25.0}
        )

        result = await mock_health_checker.get_health_status()

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "uptime" in result
        assert "version" in result
        assert "checks" in result
        assert result["checks"]["database"]["status"] == "healthy"
        assert result["checks"]["redis"]["status"] == "healthy"
        assert result["checks"]["system"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_health_status_unhealthy(self, mock_health_checker):
        """Test health status when one component has error."""
        # Mock database check to return error
        mock_health_checker._check_database = AsyncMock(
            return_value={"status": "error", "error": "Connection failed"}
        )
        mock_health_checker._check_redis = AsyncMock(
            return_value={"status": "healthy", "connection_time": 0.05}
        )
        mock_health_checker._check_system_resources = AsyncMock(
            return_value={"status": "healthy", "cpu_percent": 25.0}
        )

        result = await mock_health_checker.get_health_status()

        assert result["status"] == "unhealthy"
        assert result["checks"]["database"]["status"] == "error"
        assert result["checks"]["redis"]["status"] == "healthy"
        assert result["checks"]["system"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_health_status_degraded(self, mock_health_checker):
        """Test health status when one component has warning."""
        # Mock system check to return warning
        mock_health_checker._check_database = AsyncMock(
            return_value={"status": "healthy", "connection_time": 0.1}
        )
        mock_health_checker._check_redis = AsyncMock(
            return_value={"status": "healthy", "connection_time": 0.05}
        )
        mock_health_checker._check_system_resources = AsyncMock(
            return_value={"status": "warning", "cpu_percent": 85.0}
        )

        result = await mock_health_checker.get_health_status()

        assert result["status"] == "degraded"
        assert result["checks"]["system"]["status"] == "warning"

    @pytest.mark.asyncio
    async def test_get_health_status_with_details(self, mock_health_checker):
        """Test health status with detailed metrics."""
        # Mock all checks
        mock_health_checker._check_database = AsyncMock(
            return_value={"status": "healthy"}
        )
        mock_health_checker._check_redis = AsyncMock(return_value={"status": "healthy"})
        mock_health_checker._check_system_resources = AsyncMock(
            return_value={"status": "healthy"}
        )
        mock_health_checker._get_detailed_metrics = AsyncMock(
            return_value={"application": {"name": "Test RPG API"}}
        )

        result = await mock_health_checker.get_health_status(include_details=True)

        assert "details" in result
        assert result["details"]["application"]["name"] == "Test RPG API"

    @pytest.mark.asyncio
    async def test_check_database_healthy(self, mock_health_checker):
        """Test database health check when healthy."""
        mock_engine = Mock()
        mock_conn = AsyncMock()
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_result.scalar.return_value = "PostgreSQL 13.0"

        mock_conn.execute.return_value = mock_result
        
        # Mock async context manager properly
        async_context_manager = AsyncMock()
        async_context_manager.__aenter__ = AsyncMock(return_value=mock_conn)
        async_context_manager.__aexit__ = AsyncMock(return_value=None)
        mock_engine.begin.return_value = async_context_manager

        with patch("app.core.health.get_engine", return_value=mock_engine):
            result = await mock_health_checker._check_database()

        assert result["status"] == "healthy"
        assert "connection_time" in result
        assert result["connection_time"] < 1.0  # Should be fast for mocked call

    @pytest.mark.asyncio
    async def test_check_database_error(self, mock_health_checker):
        """Test database health check when error occurs."""
        mock_engine = Mock()
        mock_engine.begin.side_effect = Exception("Database connection failed")

        with patch("app.core.health.get_engine", return_value=mock_engine):
            result = await mock_health_checker._check_database()

        assert result["status"] == "error"
        assert "error" in result
        assert "Database connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_check_redis_healthy(self, mock_health_checker):
        """Test Redis health check when healthy."""
        mock_redis_client = Mock()
        mock_health_checker.redis_client = mock_redis_client

        # Mock asyncio.to_thread calls
        async def mock_to_thread(func, *args):
            if func == mock_redis_client.ping:
                return True
            elif func == mock_redis_client.info:
                section = args[0] if args else None
                return {
                    "memory": {"used_memory_human": "10M", "maxmemory_human": "100M"},
                    "keyspace": {"db0": {"keys": 42}},
                    None: {
                        "redis_version": "6.2.0",
                        "connected_clients": 5,
                        "uptime_in_seconds": 3600,
                    }
                }.get(section, {})
        
        with patch("asyncio.to_thread", side_effect=mock_to_thread):
            result = await mock_health_checker._check_redis()

        assert result["status"] == "healthy"
        assert "connection_time" in result
        assert "version" in result
        assert "key_count" in result

    @pytest.mark.asyncio
    async def test_check_redis_no_client(self, mock_health_checker):
        """Test Redis health check when client not initialized."""
        mock_health_checker.redis_client = None

        result = await mock_health_checker._check_redis()

        assert result["status"] == "error"
        assert "Redis client not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_check_redis_error(self, mock_health_checker):
        """Test Redis health check when error occurs."""
        mock_redis_client = Mock()
        mock_health_checker.redis_client = mock_redis_client

        async def mock_ping_error():
            raise Exception("Redis connection failed")

        with patch("asyncio.to_thread", side_effect=mock_ping_error):
            result = await mock_health_checker._check_redis()

        assert result["status"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_check_system_resources_healthy(self, mock_health_checker):
        """Test system resource check when healthy."""
        mock_memory = Mock()
        mock_memory.percent = 50.0
        mock_memory.available = 8 * 1024**3  # 8GB
        mock_memory.total = 16 * 1024**3  # 16GB

        mock_disk = Mock()
        mock_disk.percent = 60.0
        mock_disk.free = 100 * 1024**3  # 100GB
        mock_disk.total = 250 * 1024**3  # 250GB

        with (
            patch("psutil.cpu_percent", return_value=30.0),
            patch("psutil.virtual_memory", return_value=mock_memory),
            patch("psutil.disk_usage", return_value=mock_disk),
        ):
            result = await mock_health_checker._check_system_resources()

        assert result["status"] == "healthy"
        assert result["cpu_percent"] == 30.0
        assert result["memory"]["percent"] == 50.0
        assert result["disk"]["percent"] == 60.0

    @pytest.mark.asyncio
    async def test_check_system_resources_warning(self, mock_health_checker):
        """Test system resource check when resources are high."""
        mock_memory = Mock()
        mock_memory.percent = 85.0  # High memory usage
        mock_memory.available = 2 * 1024**3
        mock_memory.total = 16 * 1024**3

        mock_disk = Mock()
        mock_disk.percent = 75.0
        mock_disk.free = 50 * 1024**3
        mock_disk.total = 250 * 1024**3

        with (
            patch("psutil.cpu_percent", return_value=30.0),
            patch("psutil.virtual_memory", return_value=mock_memory),
            patch("psutil.disk_usage", return_value=mock_disk),
        ):
            result = await mock_health_checker._check_system_resources()

        assert result["status"] == "warning"
        assert result["memory"]["percent"] == 85.0

    @pytest.mark.asyncio
    async def test_check_system_resources_error(self, mock_health_checker):
        """Test system resource check when resources are critical."""
        mock_memory = Mock()
        mock_memory.percent = 97.0  # Critical memory usage (>95% triggers error)
        mock_memory.available = 1 * 1024**3
        mock_memory.total = 16 * 1024**3

        mock_disk = Mock()
        mock_disk.percent = 96.0  # Critical disk usage (>95% triggers error)
        mock_disk.free = 50 * 1024**3
        mock_disk.total = 250 * 1024**3

        with (
            patch("psutil.cpu_percent", return_value=97.0),  # Critical CPU usage
            patch("psutil.virtual_memory", return_value=mock_memory),
            patch("psutil.disk_usage", return_value=mock_disk),
        ):
            result = await mock_health_checker._check_system_resources()

        assert result["status"] == "error"
        assert result["memory"]["percent"] == 97.0

    @pytest.mark.asyncio
    async def test_get_detailed_metrics(self, mock_health_checker):
        """Test getting detailed application metrics."""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.memory_info.return_value._asdict.return_value = {
            "rss": 100 * 1024 * 1024,  # 100MB
            "vms": 200 * 1024 * 1024,  # 200MB
        }
        mock_process.cpu_percent.return_value = 15.5
        mock_process.create_time.return_value = 1640995200.0
        mock_process.num_threads.return_value = 8

        with patch("psutil.Process", return_value=mock_process):
            result = await mock_health_checker._get_detailed_metrics()

        assert "application" in result
        assert "configuration" in result
        assert "process" in result
        assert result["process"]["pid"] == 12345
        assert result["process"]["cpu_percent"] == 15.5
        assert result["process"]["num_threads"] == 8

    @pytest.mark.asyncio
    async def test_is_ready_healthy(self, mock_health_checker):
        """Test readiness check when system is healthy."""
        mock_health_checker.get_health_status = AsyncMock(
            return_value={"status": "healthy"}
        )

        result = await mock_health_checker.is_ready()

        assert result is True

    @pytest.mark.asyncio
    async def test_is_ready_degraded(self, mock_health_checker):
        """Test readiness check when system is degraded but still ready."""
        mock_health_checker.get_health_status = AsyncMock(
            return_value={"status": "degraded"}
        )

        result = await mock_health_checker.is_ready()

        assert result is True

    @pytest.mark.asyncio
    async def test_is_ready_unhealthy(self, mock_health_checker):
        """Test readiness check when system is unhealthy."""
        mock_health_checker.get_health_status = AsyncMock(
            return_value={"status": "unhealthy"}
        )

        result = await mock_health_checker.is_ready()

        assert result is False

    @pytest.mark.asyncio
    async def test_is_ready_exception(self, mock_health_checker):
        """Test readiness check when exception occurs."""
        mock_health_checker.get_health_status = AsyncMock(
            side_effect=Exception("Health check failed")
        )

        result = await mock_health_checker.is_ready()

        assert result is False

    @pytest.mark.asyncio
    async def test_is_alive(self, mock_health_checker):
        """Test liveness check (should always return True)."""
        result = await mock_health_checker.is_alive()

        assert result is True


class TestGlobalHealthChecker:
    """Test the global health checker instance."""

    def test_global_instance_exists(self):
        """Test that global health checker instance exists."""

        assert health_checker is not None
        assert isinstance(health_checker, HealthChecker)

    def test_global_instance_has_start_time(self):
        """Test that global instance has start time set."""

        assert hasattr(health_checker, "start_time")
        assert health_checker.start_time > 0
