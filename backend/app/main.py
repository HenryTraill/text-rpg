"""
Main FastAPI application entry point for the Text RPG API.

This module sets up the FastAPI application with:
- Database connection management
- Authentication and security middleware
- API versioning and routing
- Rate limiting and CORS
- Health check endpoints
- Request/response logging
- Application lifecycle events
"""

from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone

from .core.config import settings
from .core.database import create_db_and_tables, close_db_connection, check_database_health
from .core.seeder import seed_database
from .core.middleware import setup_middleware
from .core.rate_limiting import rate_limiter, add_rate_limit_headers, check_rate_limit
from .api.auth import router as auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    
    # Close Redis connection
    await rate_limiter.close()
    logger.info("Redis connection closed")
    
    # Close database connection
    await close_db_connection()
    logger.info("Database connection closed")
    
    logger.info("Text RPG API shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A medieval fantasy text-based MMO RPG API with comprehensive authentication and security",
    lifespan=lifespan,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None
)

# Setup middleware (CORS, security headers, logging, etc.)
setup_middleware(app)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Text RPG API",
        "version": settings.app_version,
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {
            "authentication": True,
            "rate_limiting": True,
            "security_headers": True,
            "request_logging": True
        }
    }


@app.get("/health")
async def health_check():
    """
    Basic health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Basic health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.app_version
    }


@app.get("/health/detailed")
async def detailed_health_check(request: Request, response: Response):
    """
    Detailed health check endpoint with dependency status.
    
    Returns:
        dict: Comprehensive health status including database and Redis connectivity
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.app_version,
        "checks": {}
    }
    
    # Check database health
    try:
        db_healthy = await check_database_health()
        health_status["checks"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": "Database connection successful" if db_healthy else "Database connection failed"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database check failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Check Redis health
    try:
        redis = await rate_limiter.get_redis()
        await redis.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis check failed: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # Add system info
    health_status["system"] = {
        "debug_mode": settings.debug,
        "rate_limit": settings.api_rate_limit,
        "max_characters_per_user": settings.max_characters_per_user
    }
    
    # Set appropriate HTTP status code
    if health_status["status"] == "unhealthy":
        response.status_code = 503
    
    return health_status


@app.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        dict: Readiness status
    """
    # Check if all critical services are ready
    try:
        db_healthy = await check_database_health()
        if not db_healthy:
            return {"status": "not_ready", "reason": "database_not_ready"}, 503
        
        redis = await rate_limiter.get_redis()
        await redis.ping()
        
        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        return {
            "status": "not_ready",
            "reason": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, 503


@app.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        dict: Liveness status
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/info")
async def api_info(
    request: Request,
    response: Response,
    rate_limit: dict = Depends(lambda r: check_rate_limit(r, limit=50, window=60))
):
    """
    API information endpoint with rate limiting.
    
    Returns:
        dict: Detailed API information and configuration
    """
    # Add rate limit headers
    await add_rate_limit_headers(response, rate_limit)
    
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "authentication": {
            "jwt_enabled": True,
            "refresh_tokens": True,
            "session_management": True,
            "password_requirements": {
                "min_length": 8,
                "requires_letter": True,
                "requires_number": True
            }
        },
        "rate_limiting": {
            "enabled": True,
            "default_limit": settings.api_rate_limit,
            "window_seconds": 60
        },
        "security": {
            "security_headers": True,
            "cors_enabled": True,
            "https_required": not settings.debug
        },
        "features": {
            "character_management": True,
            "skill_system": True,
            "inventory": True,
            "world_system": True,
            "combat": True,
            "social_features": True,
            "chat": True,
            "economy": True
        },
        "limits": {
            "max_characters_per_user": settings.max_characters_per_user,
            "websocket_max_connections": settings.websocket_max_connections,
            "chat_message_history_limit": settings.chat_message_history_limit
        },
        "endpoints": {
            "authentication": "/api/v1/auth",
            "health_checks": ["/health", "/health/detailed", "/health/ready", "/health/live"],
            "documentation": "/docs" if settings.debug else "disabled"
        }
    }


# API v1 routes
@app.get("/api/v1")
async def api_v1_info():
    """API v1 information endpoint."""
    return {
        "version": "1.0",
        "status": "stable",
        "available_endpoints": {
            "authentication": "/api/v1/auth",
            "characters": "/api/v1/characters (coming soon)",
            "skills": "/api/v1/skills (coming soon)",
            "inventory": "/api/v1/inventory (coming soon)",
            "world": "/api/v1/world (coming soon)",
            "combat": "/api/v1/combat (coming soon)",
            "social": "/api/v1/social (coming soon)",
            "chat": "/api/v1/chat (coming soon)",
            "economy": "/api/v1/economy (coming soon)"
        }
    }


# Include API routers with versioning
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

# Future routers will be added here as they are implemented:
# app.include_router(character_router, prefix="/api/v1/characters", tags=["Characters"])
# app.include_router(skill_router, prefix="/api/v1/skills", tags=["Skills"])
# app.include_router(inventory_router, prefix="/api/v1/inventory", tags=["Inventory"])
# app.include_router(world_router, prefix="/api/v1/world", tags=["World"])
# app.include_router(combat_router, prefix="/api/v1/combat", tags=["Combat"])
# app.include_router(social_router, prefix="/api/v1/social", tags=["Social"])
# app.include_router(chat_router, prefix="/api/v1/chat", tags=["Chat"])
# app.include_router(economy_router, prefix="/api/v1/economy", tags=["Economy"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )