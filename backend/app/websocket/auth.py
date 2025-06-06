"""
WebSocket Authentication

Handles JWT token validation and user authentication for WebSocket connections.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketException, status
from jose import JWTError

from app.core.auth import verify_token
from app.models.user import User
from app.core.database import get_session

logger = logging.getLogger(__name__)


class WebSocketAuthError(Exception):
    """Custom exception for WebSocket authentication errors."""
    pass


async def authenticate_websocket(
    websocket: WebSocket, 
    token: Optional[str] = None
) -> Optional[User]:
    """
    Authenticate WebSocket connection using JWT token.
    
    Args:
        websocket: FastAPI WebSocket instance
        token: JWT token from query parameters or headers
        
    Returns:
        User object if authenticated, None for anonymous connections
        
    Raises:
        WebSocketException: If authentication fails
    """
    if not token:
        # Allow anonymous connections for some channels
        logger.debug("Anonymous WebSocket connection (no token provided)")
        return None
    
    try:
        # Verify JWT token
        payload = verify_token(token)
        user_id = UUID(payload.get("sub"))
        
        # Get user from database
        with get_session() as session:
            user = session.get(User, user_id)
            if not user or not user.is_active:
                raise WebSocketAuthError("User not found or inactive")
        
        logger.info(f"WebSocket authenticated for user: {user.username}")
        return user
        
    except (JWTError, ValueError, WebSocketAuthError) as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Authentication failed"
        )
    except Exception as e:
        logger.error(f"Unexpected error during WebSocket authentication: {e}")
        raise WebSocketException(
            code=status.WS_1011_INTERNAL_ERROR,
            reason="Internal server error"
        )


def extract_token_from_websocket(websocket: WebSocket) -> Optional[str]:
    """
    Extract JWT token from WebSocket connection.
    
    Checks query parameters and headers for token.
    
    Args:
        websocket: FastAPI WebSocket instance
        
    Returns:
        JWT token string or None
    """
    # Check query parameters first
    token = websocket.query_params.get("token")
    if token:
        return token
    
    # Check headers
    authorization = websocket.headers.get("authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]  # Remove "Bearer " prefix
    
    # Check specific WebSocket token header
    ws_token = websocket.headers.get("ws-token")
    if ws_token:
        return ws_token
    
    return None


async def validate_channel_access(user: Optional[User], channel: str) -> bool:
    """
    Validate if user has access to specific WebSocket channel.
    
    Args:
        user: Authenticated user (None for anonymous)
        channel: Channel name (game, chat, combat, world)
        
    Returns:
        True if access allowed, False otherwise
    """
    # Define channel access rules
    channel_rules = {
        "game": True,  # Public channel
        "world": True,  # Public channel
        "chat": user is not None,  # Requires authentication
        "combat": user is not None,  # Requires authentication
    }
    
    # Check if channel exists
    if channel not in channel_rules:
        logger.warning(f"Access attempted to unknown channel: {channel}")
        return False
    
    # Check access rule
    has_access = channel_rules[channel]
    if isinstance(has_access, bool):
        return has_access
    
    # For more complex rules (future expansion)
    return False


async def periodic_token_validation(connection_id: str, token: str) -> bool:
    """
    Periodically validate token for long-running WebSocket connections.
    
    Args:
        connection_id: WebSocket connection ID
        token: JWT token to validate
        
    Returns:
        True if token is still valid, False otherwise
    """
    try:
        payload = verify_token(token)
        user_id = UUID(payload.get("sub"))
        
        # Additional checks for user status
        with get_session() as session:
            user = session.get(User, user_id)
            if not user or not user.is_active:
                logger.warning(f"User {user_id} no longer active, invalidating WebSocket connection {connection_id}")
                return False
        
        return True
        
    except Exception as e:
        logger.warning(f"Token validation failed for connection {connection_id}: {e}")
        return False


class WebSocketPermissions:
    """Handle WebSocket-specific permissions."""
    
    @staticmethod
    def can_send_message(user: Optional[User], channel: str) -> bool:
        """Check if user can send messages to channel."""
        if not user:
            return channel in ["game", "world"]  # Anonymous can send to public channels
        
        # Authenticated users can send to all channels
        return True
    
    @staticmethod
    def can_subscribe_to_private_messages(user: Optional[User], target_user_id: UUID) -> bool:
        """Check if user can subscribe to private messages with another user."""
        if not user:
            return False
        
        # Users can only subscribe to their own private message channels
        return user.id == target_user_id
    
    @staticmethod
    def can_access_guild_channel(user: Optional[User], guild_id: UUID) -> bool:
        """Check if user can access guild-specific channels."""
        if not user:
            return False
        
        # TODO: Check if user is member of the guild
        # This would require guild membership lookup
        return True  # Placeholder - implement guild membership check
    
    @staticmethod
    def can_moderate_channel(user: Optional[User], channel: str) -> bool:
        """Check if user has moderation permissions for channel."""
        if not user:
            return False
        
        # Check user role for moderation permissions
        return user.role in ["admin", "moderator"]