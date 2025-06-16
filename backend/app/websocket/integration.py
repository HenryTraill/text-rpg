"""
WebSocket Integration

Integrates WebSocket functionality with the main FastAPI application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.websocket.endpoints import router as websocket_router
from app.websocket.health import (
    initialize_websocket_health,
    shutdown_websocket_health,
    get_websocket_health,
    get_websocket_metrics
)

logger = logging.getLogger(__name__)


def setup_websocket_routes(app: FastAPI):
    """
    Setup WebSocket routes in the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Include WebSocket router
    app.include_router(websocket_router, tags=["websocket"])
    
    # Add WebSocket health endpoints
    @app.get("/api/v1/websocket/health")
    async def websocket_health():
        """Get WebSocket system health status."""
        return get_websocket_health()
    
    @app.get("/api/v1/websocket/metrics")
    async def websocket_metrics():
        """Get WebSocket system metrics."""
        return get_websocket_metrics()
    
    logger.info("WebSocket routes configured")


@asynccontextmanager
async def websocket_lifespan(app: FastAPI):
    """
    WebSocket lifespan manager for FastAPI application.
    
    Handles startup and shutdown of WebSocket services.
    """
    # Startup
    logger.info("Starting WebSocket services")
    try:
        await initialize_websocket_health()
        logger.info("WebSocket services started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to start WebSocket services: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down WebSocket services")
        try:
            await shutdown_websocket_health()
            logger.info("WebSocket services shut down successfully")
        except Exception as e:
            logger.error(f"Error during WebSocket shutdown: {e}")


def configure_websocket_app(app: FastAPI):
    """
    Configure WebSocket functionality for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Setup routes
    setup_websocket_routes(app)
    
    # Note: The lifespan manager needs to be set during app creation
    # This function is for documentation and reference
    logger.info("WebSocket application configuration completed")