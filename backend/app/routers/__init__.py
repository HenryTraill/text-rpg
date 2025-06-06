"""
Routers package for API endpoints.

This package contains FastAPI routers for:
- Authentication and user management
- Character management (future)
- Game features (future)
"""

from .auth import router as auth_router

__all__ = [
    "auth_router"
] 