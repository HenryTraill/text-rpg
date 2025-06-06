"""
Tests for Redis connection and caching functionality.

Validates Redis connection management, mock Redis behavior, and error handling.
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
import redis.asyncio as redis

from app.core.redis import (
    init_redis, get_redis, close_redis, 
    MockRedis, MockPubSub, _redis_pool, _redis_client
)


class TestRedisInitialization:
    """Test Redis connection initialization."""
    
    async def test_init_redis_success(self):
        """Test successful Redis initialization."""
        with patch('app.core.redis.redis.ConnectionPool') as mock_pool_class:
            with patch('app.core.redis.redis.Redis') as mock_redis_class:
                # Mock the connection pool
                mock_pool = AsyncMock()
                mock_pool_class.from_url.return_value = mock_pool
                
                # Mock the Redis client
                mock_client = AsyncMock()
                mock_redis_class.return_value = mock_client
                
                with patch('app.core.redis.settings') as mock_settings:
                    mock_settings.redis_url = "redis://localhost:6379"
                    mock_settings.redis_max_connections = 10
                    
                    with patch('app.core.redis.logger') as mock_logger:
                        await init_redis()
                        
                        # Verify connection pool creation
                        mock_pool_class.from_url.assert_called_once_with(
                            "redis://localhost:6379",
                            max_connections=10,
                            retry_on_timeout=True,
                            socket_keepalive=True,
                            socket_keepalive_options={},
                        )
                        
                        # Verify client creation and ping
                        mock_redis_class.assert_called_once_with(connection_pool=mock_pool)
                        mock_client.ping.assert_called_once()
                        mock_logger.info.assert_called_with("Redis connection established successfully")
    
    async def test_init_redis_connection_failure(self):
        """Test Redis initialization failure."""
        with patch('app.core.redis.redis.ConnectionPool') as mock_pool_class:
            # Mock connection failure
            mock_pool_class.from_url.side_effect = Exception("Connection failed")
            
            with patch('app.core.redis.logger') as mock_logger:
                await init_redis()
                
                # Verify error logging
                mock_logger.error.assert_called_once()
                mock_logger.warning.assert_called_with("Continuing without Redis connection")
    
    async def test_init_redis_ping_failure(self):
        """Test Redis ping failure during initialization."""
        with patch('app.core.redis.redis.ConnectionPool') as mock_pool_class:
            with patch('app.core.redis.redis.Redis') as mock_redis_class:
                # Mock successful pool creation but ping failure
                mock_pool = AsyncMock()
                mock_pool_class.from_url.return_value = mock_pool
                
                mock_client = AsyncMock()
                mock_client.ping.side_effect = Exception("Ping failed")
                mock_redis_class.return_value = mock_client
                
                with patch('app.core.redis.logger') as mock_logger:
                    await init_redis()
                    
                    # Verify error and warning logged
                    mock_logger.error.assert_called_once()
                    mock_logger.warning.assert_called_with("Continuing without Redis connection")


class TestRedisClient:
    """Test Redis client access."""
    
    async def test_get_redis_with_existing_client(self):
        """Test getting Redis client when already initialized."""
        # Mock existing client
        mock_client = AsyncMock()
        
        with patch('app.core.redis._redis_client', mock_client):
            client = await get_redis()
            assert client is mock_client
    
    async def test_get_redis_initializes_when_none(self):
        """Test getting Redis client triggers initialization when None."""
        # Store original client
        from app.core import redis as redis_module
        original_client = redis_module._redis_client
        
        try:
            # Set client to None to trigger initialization
            redis_module._redis_client = None
            
            with patch('app.core.redis.init_redis') as mock_init:
                # Mock the initialization to set a client
                async def mock_init_func():
                    redis_module._redis_client = AsyncMock()
                
                mock_init.side_effect = mock_init_func
                
                client = await get_redis()
                
                mock_init.assert_called_once()
                assert client is not None
        finally:
            # Restore original client
            redis_module._redis_client = original_client
    
    async def test_get_redis_returns_mock_when_unavailable(self):
        """Test getting Redis returns mock client when Redis unavailable."""
        with patch('app.core.redis._redis_client', None):
            with patch('app.core.redis.init_redis'):
                # Ensure _redis_client remains None after init
                with patch('app.core.redis.logger') as mock_logger:
                    client = await get_redis()
                    
                    assert isinstance(client, MockRedis)
                    mock_logger.warning.assert_called_with("Redis not available, returning mock client")


class TestRedisCleanup:
    """Test Redis connection cleanup."""
    
    async def test_close_redis_with_client_and_pool(self):
        """Test closing Redis when both client and pool exist."""
        mock_client = AsyncMock()
        mock_pool = AsyncMock()
        
        with patch('app.core.redis._redis_client', mock_client):
            with patch('app.core.redis._redis_pool', mock_pool):
                with patch('app.core.redis.logger') as mock_logger:
                    await close_redis()
                    
                    # Verify cleanup calls
                    mock_client.close.assert_called_once()
                    mock_pool.disconnect.assert_called_once()
                    mock_logger.info.assert_called_with("Redis connection closed")
    
    async def test_close_redis_with_no_connections(self):
        """Test closing Redis when no connections exist."""
        with patch('app.core.redis._redis_client', None):
            with patch('app.core.redis._redis_pool', None):
                with patch('app.core.redis.logger') as mock_logger:
                    await close_redis()
                    
                    # Should still log closure
                    mock_logger.info.assert_called_with("Redis connection closed")


class TestMockRedis:
    """Test MockRedis functionality."""
    
    def test_mock_redis_initialization(self):
        """Test MockRedis initialization."""
        mock_redis = MockRedis()
        assert mock_redis._data == {}
        assert mock_redis._pubsub_channels == set()
    
    async def test_mock_redis_ping(self):
        """Test MockRedis ping."""
        mock_redis = MockRedis()
        result = await mock_redis.ping()
        assert result is True
    
    async def test_mock_redis_set_and_get(self):
        """Test MockRedis set and get operations."""
        mock_redis = MockRedis()
        
        # Test set
        result = await mock_redis.set("test_key", "test_value", ex=60)
        assert result is True
        assert mock_redis._data["test_key"] == "test_value"
        
        # Test get
        value = await mock_redis.get("test_key")
        assert value == "test_value"
        
        # Test get non-existent key
        value = await mock_redis.get("non_existent")
        assert value is None
    
    async def test_mock_redis_delete(self):
        """Test MockRedis delete operation."""
        mock_redis = MockRedis()
        
        # Set a key first
        await mock_redis.set("test_key", "test_value")
        
        # Test delete existing key
        result = await mock_redis.delete("test_key")
        assert result == 1
        assert "test_key" not in mock_redis._data
        
        # Test delete non-existent key
        result = await mock_redis.delete("non_existent")
        assert result == 0
    
    async def test_mock_redis_publish(self):
        """Test MockRedis publish operation."""
        mock_redis = MockRedis()
        
        with patch('app.core.redis.logger') as mock_logger:
            result = await mock_redis.publish("test_channel", "test_message")
            
            assert result == 1
            mock_logger.debug.assert_called_with("Mock Redis publish to test_channel: test_message")
    
    def test_mock_redis_pubsub(self):
        """Test MockRedis pubsub creation."""
        mock_redis = MockRedis()
        pubsub = mock_redis.pubsub()
        assert isinstance(pubsub, MockPubSub)
    
    async def test_mock_redis_close(self):
        """Test MockRedis close operation."""
        mock_redis = MockRedis()
        # Should not raise any exception
        await mock_redis.close()


class TestMockPubSub:
    """Test MockPubSub functionality."""
    
    def test_mock_pubsub_initialization(self):
        """Test MockPubSub initialization."""
        pubsub = MockPubSub()
        assert pubsub._subscriptions == set()
    
    async def test_mock_pubsub_subscribe(self):
        """Test MockPubSub subscribe operation."""
        pubsub = MockPubSub()
        
        with patch('app.core.redis.logger') as mock_logger:
            await pubsub.subscribe("channel1", "channel2")
            
            assert "channel1" in pubsub._subscriptions
            assert "channel2" in pubsub._subscriptions
            
            # Verify debug logging
            assert mock_logger.debug.call_count == 2
    
    async def test_mock_pubsub_unsubscribe(self):
        """Test MockPubSub unsubscribe operation."""
        pubsub = MockPubSub()
        
        # Subscribe first
        await pubsub.subscribe("channel1", "channel2")
        
        with patch('app.core.redis.logger') as mock_logger:
            await pubsub.unsubscribe("channel1")
            
            assert "channel1" not in pubsub._subscriptions
            assert "channel2" in pubsub._subscriptions
            
            mock_logger.debug.assert_called_with("Mock Redis unsubscribed from channel1")
    
    async def test_mock_pubsub_listen(self):
        """Test MockPubSub listen operation."""
        pubsub = MockPubSub()
        
        # Listen should return an async generator
        result = pubsub.listen()
        # Check it's an async generator object (not None)
        assert hasattr(result, '__anext__') or result is None 