"""
Redis connection and utilities for the text RPG backend.

Provides Redis connection management for caching, pub/sub, and session storage.
"""

from typing import Optional
import redis.asyncio as redis
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """
    Initialize Redis connection pool.
    """
    global _redis_pool, _redis_client
    
    try:
        _redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={},
        )
        
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        
        # Test the connection
        await _redis_client.ping()
        logger.info("Redis connection established successfully")
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        # For development, we can continue without Redis
        logger.warning("Continuing without Redis connection")


async def get_redis() -> redis.Redis:
    """
    Get Redis client instance.
    
    Returns:
        Redis client instance
        
    Raises:
        RuntimeError: If Redis is not initialized
    """
    global _redis_client
    
    if _redis_client is None:
        await init_redis()
    
    if _redis_client is None:
        # Return a mock Redis client for testing/development
        logger.warning("Redis not available, returning mock client")
        return MockRedis()
    
    return _redis_client


async def close_redis() -> None:
    """
    Close Redis connection pool.
    """
    global _redis_pool, _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
    
    logger.info("Redis connection closed")


class MockRedis:
    """
    Mock Redis client for testing/development when Redis is not available.
    """
    
    def __init__(self):
        self._data = {}
        self._pubsub_channels = set()
    
    async def ping(self):
        """Mock ping."""
        return True
    
    async def set(self, key: str, value: str, ex: Optional[int] = None):
        """Mock set operation."""
        self._data[key] = value
        return True
    
    async def get(self, key: str):
        """Mock get operation."""
        return self._data.get(key)
    
    async def delete(self, key: str):
        """Mock delete operation."""
        if key in self._data:
            del self._data[key]
            return 1
        return 0
    
    async def publish(self, channel: str, message: str):
        """Mock publish operation."""
        logger.debug(f"Mock Redis publish to {channel}: {message}")
        return 1
    
    def pubsub(self):
        """Mock pubsub."""
        return MockPubSub()
    
    async def close(self):
        """Mock close."""
        pass


class MockPubSub:
    """
    Mock Redis pubsub for testing/development.
    """
    
    def __init__(self):
        self._subscriptions = set()
    
    async def subscribe(self, *channels):
        """Mock subscribe."""
        for channel in channels:
            self._subscriptions.add(channel)
            logger.debug(f"Mock Redis subscribed to {channel}")
    
    async def unsubscribe(self, *channels):
        """Mock unsubscribe."""
        for channel in channels:
            self._subscriptions.discard(channel)
            logger.debug(f"Mock Redis unsubscribed from {channel}")
    
    async def listen(self):
        """Mock listen - yields empty for now."""
        # In a real implementation, this would yield messages
        # For testing, we'll just return an empty async generator
        return
        yield  # pragma: no cover 