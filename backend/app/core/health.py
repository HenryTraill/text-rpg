"""
Enhanced health check system for comprehensive monitoring.

This module provides:
- Database connectivity checks
- Redis connectivity checks
- Application metrics
- Performance monitoring
- System status reporting
"""

import time
import psutil
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
import redis
from sqlmodel import text
import logging

from .config import settings
from .database import get_engine

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Comprehensive health checker for system monitoring.

    Provides health checks for:
    - Database connectivity and performance
    - Redis connectivity and performance
    - Application metrics
    - System resources
    """

    def __init__(self):
        self.start_time = time.time()
        self.redis_client = None
        self._init_redis_client()

    def _init_redis_client(self):
        """Initialize Redis client for health checks."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Redis client: {e}")

    async def get_health_status(self, include_details: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive health status.

        Args:
            include_details: Include detailed metrics and diagnostics

        Returns:
            Health status dictionary
        """
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": time.time() - self.start_time,
            "version": settings.app_version,
            "checks": {},
        }

        # Run health checks
        checks = await asyncio.gather(
            self._check_database(),
            self._check_redis(),
            self._check_system_resources(),
            return_exceptions=True,
        )

        # Process results
        health_data["checks"]["database"] = (
            checks[0]
            if not isinstance(checks[0], Exception)
            else {"status": "error", "error": str(checks[0])}
        )
        health_data["checks"]["redis"] = (
            checks[1]
            if not isinstance(checks[1], Exception)
            else {"status": "error", "error": str(checks[1])}
        )
        health_data["checks"]["system"] = (
            checks[2]
            if not isinstance(checks[2], Exception)
            else {"status": "error", "error": str(checks[2])}
        )

        # Determine overall status
        if any(
            check.get("status") == "error" for check in health_data["checks"].values()
        ):
            health_data["status"] = "unhealthy"
        elif any(
            check.get("status") == "warning" for check in health_data["checks"].values()
        ):
            health_data["status"] = "degraded"

        # Add detailed metrics if requested
        if include_details:
            health_data["details"] = await self._get_detailed_metrics()

        return health_data

    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()

            # Get database engine
            engine = get_engine()

            # Test basic connectivity
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()

            connection_time = time.time() - start_time

            # Get database info
            async with engine.begin() as conn:
                # Get database version
                version_result = await conn.execute(text("SELECT version()"))
                db_version = version_result.scalar()

                # Get database size
                size_result = await conn.execute(
                    text("SELECT pg_size_pretty(pg_database_size(current_database()))")
                )
                db_size = size_result.scalar()

                # Get connection count
                conn_result = await conn.execute(
                    text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                )
                active_connections = conn_result.scalar()

            # Determine status based on performance
            status = "healthy"
            if connection_time > 1.0:
                status = "warning"
            elif connection_time > 5.0:
                status = "error"

            return {
                "status": status,
                "connection_time": round(connection_time, 4),
                "version": db_version,
                "size": db_size,
                "active_connections": active_connections,
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "error", "error": str(e), "connection_time": None}

    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            if not self.redis_client:
                return {"status": "error", "error": "Redis client not initialized"}

            start_time = time.time()

            # Test basic connectivity
            await asyncio.to_thread(self.redis_client.ping)

            connection_time = time.time() - start_time

            # Get Redis info
            info = await asyncio.to_thread(self.redis_client.info)

            # Get memory usage
            memory_info = await asyncio.to_thread(self.redis_client.info, "memory")
            used_memory = memory_info.get("used_memory_human", "unknown")
            max_memory = memory_info.get("maxmemory_human", "unlimited")

            # Get key count
            db_info = await asyncio.to_thread(self.redis_client.info, "keyspace")
            key_count = 0
            if "db0" in db_info:
                db_stats = db_info["db0"]
                key_count = db_stats.get("keys", 0)

            # Determine status
            status = "healthy"
            if connection_time > 0.5:
                status = "warning"
            elif connection_time > 2.0:
                status = "error"

            return {
                "status": status,
                "connection_time": round(connection_time, 4),
                "version": info.get("redis_version", "unknown"),
                "used_memory": used_memory,
                "max_memory": max_memory,
                "key_count": key_count,
                "connected_clients": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0),
            }

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {"status": "error", "error": str(e), "connection_time": None}

    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage("/")

            # Determine status based on resource usage
            status = "healthy"
            if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
                status = "error"
            elif cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
                status = "warning"

            return {
                "status": status,
                "cpu_percent": round(cpu_percent, 2),
                "memory": {
                    "percent": round(memory.percent, 2),
                    "available": f"{memory.available // (1024**3)}GB",
                    "total": f"{memory.total // (1024**3)}GB",
                },
                "disk": {
                    "percent": round(disk.percent, 2),
                    "free": f"{disk.free // (1024**3)}GB",
                    "total": f"{disk.total // (1024**3)}GB",
                },
                "load_average": (
                    list(psutil.getloadavg()) if hasattr(psutil, "getloadavg") else None
                ),
            }

        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed application metrics."""
        try:
            # Application metrics
            metrics = {
                "application": {
                    "name": settings.app_name,
                    "version": settings.app_version,
                    "debug": settings.debug,
                    "uptime_seconds": time.time() - self.start_time,
                },
                "configuration": {
                    "database_pool_size": settings.database_pool_size,
                    "redis_max_connections": settings.redis_max_connections,
                    "api_rate_limit": settings.api_rate_limit,
                    "websocket_max_connections": settings.websocket_max_connections,
                },
            }

            # Process information
            process = psutil.Process()
            metrics["process"] = {
                "pid": process.pid,
                "memory_info": process.memory_info()._asdict(),
                "cpu_percent": process.cpu_percent(),
                "create_time": process.create_time(),
                "num_threads": process.num_threads(),
            }

            return metrics

        except Exception as e:
            logger.error(f"Failed to get detailed metrics: {e}")
            return {"error": str(e)}

    async def is_ready(self) -> bool:
        """
        Check if the application is ready to serve requests.

        Returns:
            True if ready, False otherwise
        """
        try:
            health = await self.get_health_status()
            return health["status"] in ["healthy", "degraded"]
        except Exception:
            return False

    async def is_alive(self) -> bool:
        """
        Check if the application is alive (basic liveness check).

        Returns:
            True if alive, False otherwise
        """
        return True  # If we can execute this, we're alive


# Global health checker instance
health_checker = HealthChecker()
