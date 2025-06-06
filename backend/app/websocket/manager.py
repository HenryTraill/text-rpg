"""
WebSocket Connection Manager

Handles WebSocket connections, authentication, and message broadcasting
with Redis pub/sub integration for real-time communication.
"""

import json
import logging
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
from sqlmodel import Session

from app.core.auth import verify_token
from app.core.database import get_session
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections with authentication and channel subscriptions."""
    
    def __init__(self):
        # Active connections: {connection_id: WebSocketConnection}
        self.active_connections: Dict[str, "WebSocketConnection"] = {}
        # Channel subscriptions: {channel: set(connection_ids)}
        self.channel_subscriptions: Dict[str, Set[str]] = {}
        # User to connection mapping: {user_id: set(connection_ids)}
        self.user_connections: Dict[UUID, Set[str]] = {}
        # Redis connection for pub/sub
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        
    async def initialize_redis(self):
        """Initialize Redis connection and pub/sub listener."""
        try:
            self.redis = await get_redis()
            self.pubsub = self.redis.pubsub()
            logger.info("WebSocket manager Redis connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis for WebSocket manager: {e}")
            raise
    
    async def connect(
        self, 
        websocket: WebSocket, 
        channel: str, 
        token: Optional[str] = None
    ) -> Optional[str]:
        """
        Accept WebSocket connection and authenticate user.
        
        Args:
            websocket: FastAPI WebSocket instance
            channel: Channel type (game, chat, combat, world)
            token: JWT authentication token
            
        Returns:
            Connection ID if successful, None if authentication failed
        """
        await websocket.accept()
        connection_id = str(uuid4())
        
        # Authenticate user if token provided
        user_id = None
        if token:
            try:
                payload = verify_token(token)
                user_id = UUID(payload.get("sub"))
                logger.info(f"WebSocket connection authenticated for user {user_id}")
            except Exception as e:
                logger.warning(f"WebSocket authentication failed: {e}")
                await websocket.close(code=4001, reason="Authentication failed")
                return None
        
        # Create connection object
        connection = WebSocketConnection(
            id=connection_id,
            websocket=websocket,
            channel=channel,
            user_id=user_id
        )
        
        # Store connection
        self.active_connections[connection_id] = connection
        
        # Subscribe to channel
        await self.subscribe_to_channel(connection_id, channel)
        
        # Track user connection
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket connection established: {connection_id} on channel {channel}")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """
        Handle WebSocket disconnection and cleanup.
        
        Args:
            connection_id: ID of the connection to disconnect
        """
        connection = self.active_connections.get(connection_id)
        if not connection:
            return
        
        # Remove from channel subscriptions
        for channel, subscribers in self.channel_subscriptions.items():
            subscribers.discard(connection_id)
        
        # Remove from user connections
        if connection.user_id:
            user_connections = self.user_connections.get(connection.user_id)
            if user_connections:
                user_connections.discard(connection_id)
                if not user_connections:
                    del self.user_connections[connection.user_id]
        
        # Remove active connection
        del self.active_connections[connection_id]
        
        logger.info(f"WebSocket connection disconnected: {connection_id}")
    
    async def subscribe_to_channel(self, connection_id: str, channel: str):
        """
        Subscribe connection to a channel.
        
        Args:
            connection_id: ID of the connection
            channel: Channel name to subscribe to
        """
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
            # Subscribe to Redis channel
            if self.pubsub:
                await self.pubsub.subscribe(f"ws:{channel}")
        
        self.channel_subscriptions[channel].add(connection_id)
        logger.debug(f"Connection {connection_id} subscribed to channel {channel}")
    
    async def unsubscribe_from_channel(self, connection_id: str, channel: str):
        """
        Unsubscribe connection from a channel.
        
        Args:
            connection_id: ID of the connection
            channel: Channel name to unsubscribe from
        """
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(connection_id)
            
            # If no more subscribers, unsubscribe from Redis
            if not self.channel_subscriptions[channel] and self.pubsub:
                await self.pubsub.unsubscribe(f"ws:{channel}")
                del self.channel_subscriptions[channel]
        
        logger.debug(f"Connection {connection_id} unsubscribed from channel {channel}")
    
    async def send_personal_message(self, message: dict, user_id: UUID):
        """
        Send message to specific user across all their connections.
        
        Args:
            message: Message data to send
            user_id: Target user ID
        """
        user_connections = self.user_connections.get(user_id, set())
        for connection_id in user_connections.copy():  # Copy to avoid modification during iteration
            await self.send_message_to_connection(message, connection_id)
    
    async def send_message_to_connection(self, message: dict, connection_id: str):
        """
        Send message to specific connection.
        
        Args:
            message: Message data to send
            connection_id: Target connection ID
        """
        connection = self.active_connections.get(connection_id)
        if connection:
            try:
                await connection.websocket.send_text(json.dumps(message))
            except WebSocketDisconnect:
                await self.disconnect(connection_id)
            except Exception as e:
                logger.error(f"Error sending message to connection {connection_id}: {e}")
                await self.disconnect(connection_id)
    
    async def broadcast_to_channel(self, message: dict, channel: str):
        """
        Broadcast message to all connections on a channel.
        
        Args:
            message: Message data to broadcast
            channel: Target channel name
        """
        if channel in self.channel_subscriptions:
            connection_ids = self.channel_subscriptions[channel].copy()
            for connection_id in connection_ids:
                await self.send_message_to_connection(message, connection_id)
    
    async def publish_to_redis(self, message: dict, channel: str):
        """
        Publish message to Redis channel for distribution across instances.
        
        Args:
            message: Message data to publish
            channel: Redis channel name
        """
        if self.redis:
            try:
                await self.redis.publish(f"ws:{channel}", json.dumps(message))
                logger.debug(f"Message published to Redis channel ws:{channel}")
            except Exception as e:
                logger.error(f"Error publishing to Redis channel {channel}: {e}")
    
    async def listen_to_redis(self):
        """Listen to Redis pub/sub messages and broadcast to local connections."""
        if not self.pubsub:
            logger.warning("Redis pubsub not initialized")
            return
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode("utf-8")
                    if channel.startswith("ws:"):
                        local_channel = channel[3:]  # Remove "ws:" prefix
                        try:
                            data = json.loads(message["data"])
                            await self.broadcast_to_channel(data, local_channel)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON in Redis message: {e}")
        except Exception as e:
            logger.error(f"Error listening to Redis pub/sub: {e}")
    
    async def send_heartbeat(self, connection_id: str):
        """
        Send heartbeat/ping to connection.
        
        Args:
            connection_id: Target connection ID
        """
        heartbeat_message = {
            "type": "heartbeat",
            "timestamp": json.dumps(None)  # Will be filled by current timestamp
        }
        await self.send_message_to_connection(heartbeat_message, connection_id)
    
    async def cleanup_inactive_connections(self):
        """Remove inactive/dead connections."""
        inactive_connections = []
        
        for connection_id, connection in self.active_connections.items():
            try:
                # Send ping to test connection
                await connection.websocket.ping()
            except Exception:
                # Connection is dead
                inactive_connections.append(connection_id)
        
        for connection_id in inactive_connections:
            await self.disconnect(connection_id)
        
        if inactive_connections:
            logger.info(f"Cleaned up {len(inactive_connections)} inactive connections")
    
    def get_connection_stats(self) -> dict:
        """Get current connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "authenticated_connections": len([
                c for c in self.active_connections.values() if c.user_id
            ]),
            "channel_subscriptions": {
                channel: len(subscribers) 
                for channel, subscribers in self.channel_subscriptions.items()
            },
            "user_connections": len(self.user_connections)
        }


class WebSocketConnection:
    """Represents a single WebSocket connection with metadata."""
    
    def __init__(
        self, 
        id: str, 
        websocket: WebSocket, 
        channel: str, 
        user_id: Optional[UUID] = None
    ):
        self.id = id
        self.websocket = websocket
        self.channel = channel
        self.user_id = user_id
        self.created_at = json.dumps(None)  # Will be filled with current timestamp
        self.last_activity = json.dumps(None)  # Will be filled with current timestamp
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = json.dumps(None)  # Will be filled with current timestamp


# Global connection manager instance
connection_manager = ConnectionManager()