"""
Tests for WebSocket functionality.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketState

from app.websocket.manager import ConnectionManager, WebSocketConnection
from app.websocket.auth import authenticate_websocket, validate_channel_access
from app.websocket.health import WebSocketHealthMonitor, WebSocketMetrics


class TestConnectionManager:
    """Test WebSocket ConnectionManager."""
    
    @pytest.fixture
    def connection_manager(self):
        """Create a ConnectionManager instance for testing."""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket for testing."""
        websocket = AsyncMock()
        websocket.client_state = WebSocketState.CONNECTED
        return websocket
    
    async def test_connection_manager_initialization(self, connection_manager):
        """Test ConnectionManager initialization."""
        assert connection_manager.active_connections == {}
        assert connection_manager.channel_subscriptions == {}
        assert connection_manager.user_connections == {}
    
    async def test_connect_without_authentication(self, connection_manager, mock_websocket):
        """Test connecting without authentication."""
        connection_id = await connection_manager.connect(
            websocket=mock_websocket,
            channel="game",
            token=None
        )
        
        assert connection_id is not None
        assert connection_id in connection_manager.active_connections
        assert "game" in connection_manager.channel_subscriptions
        mock_websocket.accept.assert_called_once()
    
    async def test_disconnect(self, connection_manager, mock_websocket):
        """Test disconnecting a WebSocket connection."""
        # First connect
        connection_id = await connection_manager.connect(
            websocket=mock_websocket,
            channel="game",
            token=None
        )
        
        # Then disconnect
        await connection_manager.disconnect(connection_id)
        
        assert connection_id not in connection_manager.active_connections
        assert len(connection_manager.channel_subscriptions.get("game", set())) == 0
    
    async def test_subscribe_to_channel(self, connection_manager):
        """Test subscribing to a channel."""
        connection_id = "test-connection"
        channel = "test-channel"
        
        await connection_manager.subscribe_to_channel(connection_id, channel)
        
        assert channel in connection_manager.channel_subscriptions
        assert connection_id in connection_manager.channel_subscriptions[channel]
    
    async def test_broadcast_to_channel(self, connection_manager, mock_websocket):
        """Test broadcasting message to channel."""
        # Setup connection
        connection_id = await connection_manager.connect(
            websocket=mock_websocket,
            channel="test",
            token=None
        )
        
        # Broadcast message
        message = {"type": "test", "content": "hello"}
        await connection_manager.broadcast_to_channel(message, "test")
        
        # Verify message was sent
        expected_json = json.dumps(message)
        mock_websocket.send_text.assert_called_with(expected_json)
    
    def test_get_connection_stats(self, connection_manager):
        """Test getting connection statistics."""
        stats = connection_manager.get_connection_stats()
        
        assert "total_connections" in stats
        assert "authenticated_connections" in stats
        assert "channel_subscriptions" in stats
        assert "user_connections" in stats


class TestWebSocketConnection:
    """Test WebSocketConnection class."""
    
    def test_websocket_connection_creation(self):
        """Test creating a WebSocketConnection."""
        mock_websocket = AsyncMock()
        connection = WebSocketConnection(
            id="test-id",
            websocket=mock_websocket,
            channel="test-channel"
        )
        
        assert connection.id == "test-id"
        assert connection.websocket == mock_websocket
        assert connection.channel == "test-channel"
        assert connection.user_id is None
    
    def test_websocket_connection_with_user(self):
        """Test creating a WebSocketConnection with user."""
        from uuid import uuid4
        
        mock_websocket = AsyncMock()
        user_id = uuid4()
        connection = WebSocketConnection(
            id="test-id",
            websocket=mock_websocket,
            channel="test-channel",
            user_id=user_id
        )
        
        assert connection.user_id == user_id


class TestWebSocketAuth:
    """Test WebSocket authentication functions."""
    
    async def test_validate_channel_access_public_channels(self):
        """Test channel access validation for public channels."""
        # Anonymous user can access public channels
        assert await validate_channel_access(None, "game") == True
        assert await validate_channel_access(None, "world") == True
        
        # Anonymous user cannot access private channels
        assert await validate_channel_access(None, "chat") == False
        assert await validate_channel_access(None, "combat") == False
    
    async def test_validate_channel_access_authenticated_user(self):
        """Test channel access validation for authenticated users."""
        from app.models.user import User
        from uuid import uuid4
        
        # Mock authenticated user
        user = User(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        
        # Authenticated user can access all channels
        assert await validate_channel_access(user, "game") == True
        assert await validate_channel_access(user, "world") == True
        assert await validate_channel_access(user, "chat") == True
        assert await validate_channel_access(user, "combat") == True
    
    async def test_validate_channel_access_unknown_channel(self):
        """Test channel access validation for unknown channels."""
        assert await validate_channel_access(None, "unknown") == False


class TestWebSocketHealth:
    """Test WebSocket health monitoring."""
    
    def test_websocket_health_monitor_initialization(self):
        """Test WebSocketHealthMonitor initialization."""
        monitor = WebSocketHealthMonitor()
        
        assert monitor.heartbeat_interval == 30
        assert monitor.cleanup_interval == 60
        assert monitor.connection_timeout == 120
        assert monitor.running == False
        assert len(monitor.tasks) == 0
    
    def test_websocket_metrics_initialization(self):
        """Test WebSocketMetrics initialization."""
        metrics = WebSocketMetrics()
        
        assert len(metrics.connection_count_history) == 0
        assert metrics.message_count == 0
        assert metrics.error_count == 0
        assert metrics.start_time is not None
    
    def test_websocket_metrics_record_message(self):
        """Test recording messages in metrics."""
        metrics = WebSocketMetrics()
        initial_count = metrics.message_count
        
        metrics.record_message()
        
        assert metrics.message_count == initial_count + 1
    
    def test_websocket_metrics_record_error(self):
        """Test recording errors in metrics."""
        metrics = WebSocketMetrics()
        initial_count = metrics.error_count
        
        metrics.record_error()
        
        assert metrics.error_count == initial_count + 1
    
    def test_websocket_metrics_get_metrics(self):
        """Test getting metrics data."""
        metrics = WebSocketMetrics()
        metrics.record_message()
        metrics.record_error()
        
        metrics_data = metrics.get_metrics()
        
        assert "uptime_seconds" in metrics_data
        assert "total_messages" in metrics_data
        assert "total_errors" in metrics_data
        assert "current_connections" in metrics_data
        assert metrics_data["total_messages"] == 1
        assert metrics_data["total_errors"] == 1


class TestWebSocketEndpoints:
    """Test WebSocket endpoints integration."""
    
    @pytest.fixture
    def test_client(self):
        """Create a test client for WebSocket testing."""
        from app.main import app
        return TestClient(app)
    
    def test_websocket_health_endpoint(self, test_client):
        """Test WebSocket health endpoint."""
        response = test_client.get("/api/v1/websocket/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "connections" in data
    
    def test_websocket_metrics_endpoint(self, test_client):
        """Test WebSocket metrics endpoint."""
        response = test_client.get("/api/v1/websocket/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "uptime_seconds" in data
        assert "total_messages" in data
        assert "current_connections" in data


class TestWebSocketIntegration:
    """Test full WebSocket integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self):
        """Test complete connection lifecycle."""
        manager = ConnectionManager()
        mock_websocket = AsyncMock()
        mock_websocket.client_state = WebSocketState.CONNECTED
        
        # Connect
        connection_id = await manager.connect(
            websocket=mock_websocket,
            channel="game",
            token=None
        )
        
        assert connection_id is not None
        assert len(manager.active_connections) == 1
        
        # Send message
        message = {"type": "test", "data": "hello"}
        await manager.send_message_to_connection(message, connection_id)
        
        mock_websocket.send_text.assert_called_once()
        
        # Disconnect
        await manager.disconnect(connection_id)
        
        assert len(manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_channel_broadcasting(self):
        """Test broadcasting to multiple connections on same channel."""
        manager = ConnectionManager()
        
        # Create multiple mock connections
        connections = []
        for i in range(3):
            mock_websocket = AsyncMock()
            mock_websocket.client_state = WebSocketState.CONNECTED
            connection_id = await manager.connect(
                websocket=mock_websocket,
                channel="test",
                token=None
            )
            connections.append((connection_id, mock_websocket))
        
        # Broadcast message
        message = {"type": "broadcast", "data": "hello all"}
        await manager.broadcast_to_channel(message, "test")
        
        # Verify all connections received message
        for _, mock_websocket in connections:
            mock_websocket.send_text.assert_called_once()
        
        # Cleanup
        for connection_id, _ in connections:
            await manager.disconnect(connection_id)