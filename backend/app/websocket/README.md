# WebSocket Manager System

## Overview

The WebSocket Manager System provides real-time communication capabilities for the text RPG game. It implements a comprehensive WebSocket infrastructure with authentication, Redis pub/sub integration, and multi-channel support.

## Features

### ✅ Core Features Implemented

- **WebSocket Connection Manager**: Centralized connection handling with lifecycle management
- **JWT Authentication**: Secure WebSocket connections with token validation
- **Redis Pub/Sub Integration**: Distributed message broadcasting across server instances
- **Multi-Channel Support**: Separate channels for different game features
- **Connection Pooling**: Efficient connection management and cleanup
- **Heartbeat Mechanism**: Connection health monitoring with automatic cleanup
- **Message Broadcasting**: Channel-based and user-specific message delivery
- **Graceful Error Handling**: Robust error handling and connection recovery

### 🔌 WebSocket Endpoints

#### `/ws/game` - General Game Events
- Player status updates
- Achievement notifications
- System announcements
- General game state changes
- **Authentication**: Optional (supports anonymous connections)

#### `/ws/chat` - Real-time Messaging
- Chat messages (global, guild, party, private)
- Typing indicators
- Message history requests
- Chat moderation events
- **Authentication**: Required

#### `/ws/combat` - Combat System
- Turn-based combat state synchronization
- Combat action results
- Combat timers and timeouts
- Combat participant notifications
- **Authentication**: Required

#### `/ws/world` - World Events
- Player movement updates
- Nearby player notifications
- World event announcements
- Zone change notifications
- **Authentication**: Optional (supports anonymous connections)

## Architecture

### Connection Manager (`manager.py`)
- Central hub for all WebSocket connections
- Handles authentication, channel subscriptions, and message routing
- Integrates with Redis for distributed messaging
- Provides connection statistics and health monitoring

### Authentication (`auth.py`)
- JWT token validation for WebSocket connections
- Channel access control based on user permissions
- Periodic token validation for long-running connections
- Support for anonymous connections on public channels

### Endpoints (`endpoints.py`)
- Individual WebSocket endpoint handlers for each channel
- Message type routing and validation
- Channel-specific business logic
- Error handling and connection management

### Health Monitoring (`health.py`)
- Heartbeat mechanism for connection health
- Automatic cleanup of inactive connections
- Metrics collection and monitoring
- Redis listener for distributed messages

### Integration (`integration.py`)
- FastAPI application integration
- Health and metrics endpoints
- Lifespan management for WebSocket services

## Usage

### Client Connection

```javascript
// Connect to game channel
const gameSocket = new WebSocket('ws://localhost:8000/ws/game?token=your_jwt_token');

// Connect to chat channel (authentication required)
const chatSocket = new WebSocket('ws://localhost:8000/ws/chat?token=your_jwt_token');

// Handle messages
gameSocket.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('Game event:', message);
};
```

### Authentication

```javascript
// Token in query parameter
const socket = new WebSocket('ws://localhost:8000/ws/chat?token=your_jwt_token');

// Token in headers (if WebSocket client supports)
const socket = new WebSocket('ws://localhost:8000/ws/chat', [], {
    headers: {
        'Authorization': 'Bearer your_jwt_token'
    }
});
```

### Message Types

#### Game Channel Messages
```json
{
  "type": "achievement",
  "user_id": "uuid",
  "achievement": "first_kill",
  "timestamp": "2025-06-06T16:00:00Z"
}
```

#### Chat Channel Messages
```json
{
  "type": "chat_message",
  "user": "username",
  "user_id": "uuid",
  "content": "Hello world!",
  "channel": "global",
  "timestamp": "2025-06-06T16:00:00Z"
}
```

#### Combat Channel Messages
```json
{
  "type": "combat_action",
  "user_id": "uuid",
  "action": "attack",
  "target": "monster_id",
  "combat_session_id": "uuid"
}
```

#### World Channel Messages
```json
{
  "type": "player_movement",
  "user_id": "uuid",
  "x": 100.5,
  "y": 200.3,
  "zone": "starter_town",
  "timestamp": "2025-06-06T16:00:00Z"
}
```

### Health Monitoring

```bash
# Check WebSocket system health
curl http://localhost:8000/api/v1/websocket/health

# Get WebSocket metrics
curl http://localhost:8000/api/v1/websocket/metrics
```

## Configuration

### Environment Variables

```env
# Redis configuration for pub/sub
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your_redis_password

# WebSocket settings
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_CLEANUP_INTERVAL=60
WEBSOCKET_CONNECTION_TIMEOUT=120
```

### FastAPI Integration

```python
from fastapi import FastAPI
from app.websocket.integration import configure_websocket_app, websocket_lifespan

# Create app with WebSocket lifespan
app = FastAPI(lifespan=websocket_lifespan)

# Configure WebSocket routes
configure_websocket_app(app)
```

## Testing

Run WebSocket tests:

```bash
# Run all WebSocket tests
pytest backend/tests/test_websocket.py

# Run specific test class
pytest backend/tests/test_websocket.py::TestConnectionManager

# Run with coverage
pytest backend/tests/test_websocket.py --cov=app.websocket
```

## Security

### Authentication
- JWT token validation for protected channels
- Periodic token re-validation for long connections
- Automatic disconnection for invalid/expired tokens

### Access Control
- Channel-based access control
- User role validation for moderation features
- Rate limiting integration (uses existing middleware)

### Error Handling
- Graceful handling of connection failures
- Secure error messages without sensitive information
- Automatic cleanup of dead connections

## Performance

### Connection Management
- Efficient connection pooling
- Automatic cleanup of inactive connections
- Memory-optimized message broadcasting

### Redis Integration
- Pub/sub for distributed messaging
- Connection pooling for Redis operations
- Fallback handling for Redis failures

### Monitoring
- Connection count tracking
- Message throughput metrics
- Error rate monitoring

## Future Enhancements

- [ ] Message persistence for offline users
- [ ] Advanced channel permissions
- [ ] WebSocket rate limiting
- [ ] Message encryption for sensitive channels
- [ ] WebSocket compression support
- [ ] Advanced metrics and analytics

## Dependencies

- `fastapi` - WebSocket endpoint framework
- `redis` - Pub/sub messaging
- `jose` - JWT token validation
- `sqlmodel` - Database integration
- `pytest` - Testing framework

## API Reference

### Connection Manager Methods

- `connect()` - Establish new WebSocket connection
- `disconnect()` - Clean up WebSocket connection
- `subscribe_to_channel()` - Subscribe connection to channel
- `broadcast_to_channel()` - Send message to all channel subscribers
- `send_personal_message()` - Send message to specific user
- `publish_to_redis()` - Publish message to Redis channel

### Health Monitor Methods

- `start()` - Start health monitoring services
- `stop()` - Stop health monitoring services
- `get_health_status()` - Get current system health
- `get_metrics()` - Get performance metrics