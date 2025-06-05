"""
Main FastAPI application entry point for the Text RPG API.

This module sets up the FastAPI application with:
- Database connection management
- CORS configuration
- Health check endpoints
- Application lifecycle events
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .core.config import settings
from .core.database import create_db_and_tables, close_db_connection, check_database_health
from .core.seeder import seed_database

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
    description="A medieval fantasy text-based MMO RPG API",
    lifespan=lifespan,
    debug=settings.debug
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to the Text RPG API",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Health status including database connectivity
    """
    db_healthy = await check_database_health()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "version": settings.app_version
    }


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
            "economy": True
        },
        "limits": {
            "max_characters_per_user": settings.max_characters_per_user,
            "api_rate_limit": settings.api_rate_limit,
            "websocket_max_connections": settings.websocket_max_connections
        }
    }


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )