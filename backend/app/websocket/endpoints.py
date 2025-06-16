"""
WebSocket Endpoints

Implements the WebSocket endpoints for different channels:
- /ws/game - General game events and notifications
- /ws/chat - Real-time messaging and communication
- /ws/combat - Combat updates and turn notifications  
- /ws/world - World events, movement, and spatial updates
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.websockets import WebSocketState

from app.websocket.manager import connection_manager
from app.websocket.auth import (
    authenticate_websocket,
    extract_token_from_websocket,
    validate_channel_access
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/game")
async def websocket_game_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """
    WebSocket endpoint for general game events and notifications.
    
    Handles:
    - Player status updates
    - Achievement notifications
    - System announcements
    - General game state changes
    """
    connection_id = None
    try:
        # Extract token from various sources
        if not token:
            token = extract_token_from_websocket(websocket)
        
        # Authenticate user (optional for game channel)
        user = None
        if token:
            try:
                user = await authenticate_websocket(websocket, token)
            except Exception as e:
                logger.warning(f"Game channel authentication failed, allowing anonymous: {e}")
        
        # Validate channel access
        if not await validate_channel_access(user, "game"):
            await websocket.close(code=4003, reason="Access denied")
            return
        
        # Connect to WebSocket manager
        connection_id = await connection_manager.connect(
            websocket=websocket,
            channel="game",
            token=token
        )
        
        if not connection_id:
            await websocket.close(code=4001, reason="Connection failed")
            return
        
        logger.info(f"Game WebSocket connected: {connection_id}")
        
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "channel": "game",
            "message": "Connected to game events",
            "authenticated": user is not None
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Listen for messages
        while websocket.client_state == WebSocketState.CONNECTED:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle incoming message
                await handle_game_message(connection_id, message, user)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error_msg = {"type": "error", "message": "Invalid JSON format"}
                await websocket.send_text(json.dumps(error_msg))
            except Exception as e:
                logger.error(f"Error in game WebSocket: {e}")
                error_msg = {"type": "error", "message": "Internal server error"}
                await websocket.send_text(json.dumps(error_msg))
                
    except WebSocketDisconnect:
        logger.info(f"Game WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Game WebSocket error: {e}")
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time messaging and communication.
    
    Handles:
    - Chat messages (global, guild, party, private)
    - Typing indicators
    - Message history requests
    - Chat moderation events
    """
    connection_id = None
    try:
        # Extract token
        if not token:
            token = extract_token_from_websocket(websocket)
        
        # Authenticate user (required for chat)
        user = await authenticate_websocket(websocket, token)
        if not user:
            await websocket.close(code=4001, reason="Authentication required for chat")
            return
        
        # Validate channel access
        if not await validate_channel_access(user, "chat"):
            await websocket.close(code=4003, reason="Access denied")
            return
        
        # Connect to WebSocket manager
        connection_id = await connection_manager.connect(
            websocket=websocket,
            channel="chat",
            token=token
        )
        
        if not connection_id:
            await websocket.close(code=4001, reason="Connection failed")
            return
        
        logger.info(f"Chat WebSocket connected: {connection_id} for user {user.username}")
        
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "channel": "chat",
            "message": f"Welcome to chat, {user.username}",
            "user_id": str(user.id)
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Listen for messages
        while websocket.client_state == WebSocketState.CONNECTED:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle incoming chat message
                await handle_chat_message(connection_id, message, user)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error_msg = {"type": "error", "message": "Invalid JSON format"}
                await websocket.send_text(json.dumps(error_msg))
            except Exception as e:
                logger.error(f"Error in chat WebSocket: {e}")
                error_msg = {"type": "error", "message": "Internal server error"}
                await websocket.send_text(json.dumps(error_msg))
                
    except WebSocketDisconnect:
        logger.info(f"Chat WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


@router.websocket("/ws/combat")
async def websocket_combat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """
    WebSocket endpoint for combat updates and turn notifications.
    
    Handles:
    - Turn-based combat state updates
    - Combat action results
    - Combat timers and timeouts
    - Combat participant notifications
    """
    connection_id = None
    try:
        # Extract token
        if not token:
            token = extract_token_from_websocket(websocket)
        
        # Authenticate user (required for combat)
        user = await authenticate_websocket(websocket, token)
        if not user:
            await websocket.close(code=4001, reason="Authentication required for combat")
            return
        
        # Validate channel access
        if not await validate_channel_access(user, "combat"):
            await websocket.close(code=4003, reason="Access denied")
            return
        
        # Connect to WebSocket manager
        connection_id = await connection_manager.connect(
            websocket=websocket,
            channel="combat",
            token=token
        )
        
        if not connection_id:
            await websocket.close(code=4001, reason="Connection failed")
            return
        
        logger.info(f"Combat WebSocket connected: {connection_id} for user {user.username}")
        
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "channel": "combat",
            "message": "Connected to combat system",
            "user_id": str(user.id)
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Listen for messages
        while websocket.client_state == WebSocketState.CONNECTED:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle incoming combat message
                await handle_combat_message(connection_id, message, user)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error_msg = {"type": "error", "message": "Invalid JSON format"}
                await websocket.send_text(json.dumps(error_msg))
            except Exception as e:
                logger.error(f"Error in combat WebSocket: {e}")
                error_msg = {"type": "error", "message": "Internal server error"}
                await websocket.send_text(json.dumps(error_msg))
                
    except WebSocketDisconnect:
        logger.info(f"Combat WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Combat WebSocket error: {e}")
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


@router.websocket("/ws/world")
async def websocket_world_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT authentication token")
):
    """
    WebSocket endpoint for world events, movement, and spatial updates.
    
    Handles:
    - Player movement updates
    - Nearby player notifications
    - World event announcements
    - Zone change notifications
    """
    connection_id = None
    try:
        # Extract token
        if not token:
            token = extract_token_from_websocket(websocket)
        
        # Authenticate user (optional for world channel)
        user = None
        if token:
            try:
                user = await authenticate_websocket(websocket, token)
            except Exception as e:
                logger.warning(f"World channel authentication failed, allowing anonymous: {e}")
        
        # Validate channel access
        if not await validate_channel_access(user, "world"):
            await websocket.close(code=4003, reason="Access denied")
            return
        
        # Connect to WebSocket manager
        connection_id = await connection_manager.connect(
            websocket=websocket,
            channel="world",
            token=token
        )
        
        if not connection_id:
            await websocket.close(code=4001, reason="Connection failed")
            return
        
        logger.info(f"World WebSocket connected: {connection_id}")
        
        # Send welcome message
        welcome_message = {
            "type": "welcome",
            "channel": "world",
            "message": "Connected to world events",
            "authenticated": user is not None
        }
        await websocket.send_text(json.dumps(welcome_message))
        
        # Listen for messages
        while websocket.client_state == WebSocketState.CONNECTED:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle incoming world message
                await handle_world_message(connection_id, message, user)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                error_msg = {"type": "error", "message": "Invalid JSON format"}
                await websocket.send_text(json.dumps(error_msg))
            except Exception as e:
                logger.error(f"Error in world WebSocket: {e}")
                error_msg = {"type": "error", "message": "Internal server error"}
                await websocket.send_text(json.dumps(error_msg))
                
    except WebSocketDisconnect:
        logger.info(f"World WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"World WebSocket error: {e}")
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


# Message handlers for each channel
async def handle_game_message(connection_id: str, message: dict, user):
    """Handle incoming messages on the game channel."""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        pong_message = {"type": "pong", "timestamp": message.get("timestamp")}
        await connection_manager.send_message_to_connection(pong_message, connection_id)
    
    elif message_type == "subscribe":
        # Subscribe to specific game events
        event_type = message.get("event_type")
        if event_type:
            # TODO: Implement specific event subscriptions
            logger.info(f"Game subscription request: {event_type}")
    
    else:
        logger.debug(f"Unhandled game message type: {message_type}")


async def handle_chat_message(connection_id: str, message: dict, user):
    """Handle incoming messages on the chat channel."""
    message_type = message.get("type")
    
    if message_type == "chat_message":
        # Broadcast chat message to channel
        chat_data = {
            "type": "chat_message",
            "user": user.username,
            "user_id": str(user.id),
            "content": message.get("content"),
            "channel": message.get("chat_channel", "global"),
            "timestamp": json.dumps(None)  # Will be filled with current timestamp
        }
        
        # Broadcast to chat channel
        await connection_manager.broadcast_to_channel(chat_data, "chat")
        await connection_manager.publish_to_redis(chat_data, "chat")
    
    elif message_type == "typing":
        # Broadcast typing indicator
        typing_data = {
            "type": "typing",
            "user": user.username,
            "user_id": str(user.id),
            "channel": message.get("chat_channel", "global")
        }
        await connection_manager.broadcast_to_channel(typing_data, "chat")
    
    else:
        logger.debug(f"Unhandled chat message type: {message_type}")


async def handle_combat_message(connection_id: str, message: dict, user):
    """Handle incoming messages on the combat channel."""
    message_type = message.get("type")
    
    if message_type == "combat_action":
        # Process combat action
        action_data = {
            "type": "combat_action",
            "user_id": str(user.id),
            "action": message.get("action"),
            "target": message.get("target"),
            "combat_session_id": message.get("combat_session_id")
        }
        
        # TODO: Validate and process combat action
        # For now, just broadcast the action
        await connection_manager.broadcast_to_channel(action_data, "combat")
        await connection_manager.publish_to_redis(action_data, "combat")
    
    elif message_type == "join_combat":
        # Join combat session
        join_data = {
            "type": "player_joined_combat",
            "user_id": str(user.id),
            "username": user.username,
            "combat_session_id": message.get("combat_session_id")
        }
        await connection_manager.broadcast_to_channel(join_data, "combat")
    
    else:
        logger.debug(f"Unhandled combat message type: {message_type}")


async def handle_world_message(connection_id: str, message: dict, user):
    """Handle incoming messages on the world channel."""
    message_type = message.get("type")
    
    if message_type == "movement":
        # Broadcast player movement
        movement_data = {
            "type": "player_movement",
            "user_id": str(user.id) if user else None,
            "x": message.get("x"),
            "y": message.get("y"),
            "zone": message.get("zone"),
            "timestamp": json.dumps(None)  # Will be filled with current timestamp
        }
        
        # Broadcast to world channel
        await connection_manager.broadcast_to_channel(movement_data, "world")
        await connection_manager.publish_to_redis(movement_data, "world")
    
    elif message_type == "zone_change":
        # Broadcast zone change
        zone_data = {
            "type": "zone_change",
            "user_id": str(user.id) if user else None,
            "old_zone": message.get("old_zone"),
            "new_zone": message.get("new_zone")
        }
        await connection_manager.broadcast_to_channel(zone_data, "world")
    
    else:
        logger.debug(f"Unhandled world message type: {message_type}")