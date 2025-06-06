"""
Main FastAPI application entry point for the Text RPG API.

This module sets up the FastAPI application with:
- Database connection management
- Enhanced CORS configuration
- Comprehensive middleware stack
- Authentication and authorization
- Health check endpoints
- Application lifecycle events
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .core.config import settings
from .core.database import (
    create_db_and_tables,
    close_db_connection,
)
from .core.seeder import seed_database
from .core.health import health_checker
from .middleware import LoggingMiddleware, init_rate_limiter, init_security_middleware
from .routers import auth_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Text RPG API...")

    try:
        # Create database tables
        await create_db_and_tables()
        logger.info("Database tables created successfully")

        # Seed initial data
        await seed_database()
        logger.info("Database seeding completed")

        logger.info("Text RPG API startup completed")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Text RPG API...")
    await close_db_connection()
    logger.info("Text RPG API shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A medieval fantasy text-based MMO RPG API with comprehensive authentication and security",
    lifespan=lifespan,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add middleware (order matters - reverse execution order)
# 1. Security middleware (first to execute, last to process response)
security_middleware = init_security_middleware(app)
app.add_middleware(type(security_middleware))

# 2. Rate limiting middleware
rate_limiter = init_rate_limiter(app)
app.add_middleware(type(rate_limiter))

# 3. Logging middleware
app.add_middleware(LoggingMiddleware)

# 4. Basic CORS (fallback for non-security middleware handled requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
    ],
    expose_headers=[
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Text RPG API",
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health_check(
    details: bool = Query(False, description="Include detailed health metrics"),
):
    """
    Comprehensive health check endpoint for monitoring and load balancers.

    Args:
        details: Include detailed metrics and diagnostics

    Returns:
        dict: Comprehensive health status including all system components
    """
    from fastapi import Response
    
    try:
        health_status = await health_checker.get_health_status(include_details=details)
        
        # Set appropriate HTTP status code based on health status
        if health_status.get("status") == "unhealthy":
            import json
            response = Response(
                content=json.dumps(health_status),
                status_code=503,
                media_type="application/json",
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
            )
            return response
        
        import json
        response = Response(
            content=json.dumps(health_status),
            status_code=200,
            media_type="application/json",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        return response
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        import json
        error_data = {"error": str(e)}
        response = Response(
            content=json.dumps(error_data),
            status_code=500,
            media_type="application/json",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        return response


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes and container orchestration.

    Returns:
        dict: Readiness status
    """
    from fastapi import Response
    from datetime import datetime, timezone
    import json
    
    try:
        is_ready = await health_checker.is_ready()
        
        response_data = {
            "ready": is_ready,
            "status": "ready" if is_ready else "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        status_code = 200 if is_ready else 503
        
        return Response(
            content=json.dumps(response_data),
            status_code=status_code,
            media_type="application/json",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        
        error_response = {
            "ready": False,
            "status": "not_ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }
        
        return Response(
            content=json.dumps(error_response),
            status_code=503,
            media_type="application/json",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )


@app.get("/alive")
async def liveness_check():
    """
    Liveness check endpoint for Kubernetes and container orchestration.

    Returns:
        dict: Liveness status
    """
    from fastapi import Response
    from datetime import datetime, timezone
    import json
    
    try:
        is_alive = await health_checker.is_alive()
        
        response_data = {
            "alive": is_alive,
            "status": "alive" if is_alive else "dead",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return Response(
            content=json.dumps(response_data),
            status_code=200,  # Liveness always returns 200
            media_type="application/json",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        # Liveness should always return alive (200) even on exception
        
        error_response = {
            "alive": True,
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }
        
        return Response(
            content=json.dumps(error_response),
            status_code=200,  # Liveness always returns 200
            media_type="application/json",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )


@app.get("/api/info")
async def api_info():
    """
    API information endpoint.

    Returns:
        dict: Detailed API information and configuration
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "features": {
            "authentication": True,
            "character_management": True,
            "skill_system": True,
            "inventory": True,
            "world_system": True,
            "combat": True,
            "social_features": True,
            "chat": True,
            "economy": True,
        },
        "limits": {
            "max_characters_per_user": settings.max_characters_per_user,
            "api_rate_limit": settings.api_rate_limit,
            "websocket_max_connections": settings.websocket_max_connections,
        },
    }


<<<<<<< Updated upstream
# Include API routers with versioning structure
app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])

# Future routers (will be added in future issues)
# app.include_router(character_router, prefix="/api/v1/characters", tags=["characters"])
# app.include_router(skill_router, prefix="/api/v1/skills", tags=["skills"])
# app.include_router(inventory_router, prefix="/api/v1/inventory", tags=["inventory"])
# app.include_router(world_router, prefix="/api/v1/world", tags=["world"])
# app.include_router(combat_router, prefix="/api/v1/combat", tags=["combat"])
# app.include_router(social_router, prefix="/api/v1/social", tags=["social"])
# app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
# app.include_router(economy_router, prefix="/api/v1/economy", tags=["economy"])
=======
# Include WebSocket routes
try:
    from .websocket.integration import setup_websocket_routes, get_websocket_health, get_websocket_metrics
    setup_websocket_routes(app)
    
    # Add WebSocket health endpoints
    @app.get("/api/v1/websocket/health")
    async def websocket_health():
        """Get WebSocket system health status."""
        return get_websocket_health()
    
    @app.get("/api/v1/websocket/metrics")
    async def websocket_metrics():
        """Get WebSocket system metrics."""
        return get_websocket_metrics()
        
    logger.info("WebSocket routes configured successfully")
except ImportError as e:
    logger.warning(f"WebSocket module not available: {e}")

# Include API routers (will be added in future issues)
# app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
# app.include_router(character_router, prefix="/api/characters", tags=["characters"])
# app.include_router(skill_router, prefix="/api/skills", tags=["skills"])
# app.include_router(inventory_router, prefix="/api/inventory", tags=["inventory"])
# app.include_router(world_router, prefix="/api/world", tags=["world"])
# app.include_router(combat_router, prefix="/api/combat", tags=["combat"])
# app.include_router(social_router, prefix="/api/social", tags=["social"])
# app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
# app.include_router(economy_router, prefix="/api/economy", tags=["economy"])
>>>>>>> Stashed changes


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )
