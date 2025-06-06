from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
import logging

from .config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create async engine with appropriate configuration based on database type
if settings.database_url.startswith(("sqlite", "sqlite+aiosqlite")):
    # SQLite configuration - no connection pooling
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,  # Log SQL queries in debug mode
        future=True,
    )
else:
    # PostgreSQL configuration - with connection pooling
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_recycle=settings.database_pool_recycle,
        echo=settings.debug,  # Log SQL queries in debug mode
        future=True,
    )

# Create session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def get_engine():
    """
    Get the database engine for health checks and direct access.

    Returns:
        AsyncEngine: Database engine
    """
    return engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_and_tables():
    """
    Create database tables from SQLModel metadata.
    This should be called during application startup.
    """
    async with engine.begin() as conn:
        # Import all models to ensure they're registered with SQLModel.metadata
        # This will be updated when models are created
        try:
            # Import all models to ensure they're registered with SQLModel.metadata
            from app.models.user import User  # noqa: F401
            from app.models.character import Character  # noqa: F401
            from app.models.skill import Skill, CharacterSkill  # noqa: F401
            from app.models.inventory import Item, InventorySlot  # noqa: F401
            from app.models.world import Zone, Location  # noqa: F401
            from app.models.social import Guild, GuildMember, Party, Friendship  # noqa: F401
            from app.models.chat import ChatChannel, Message  # noqa: F401
            from app.models.combat import CombatSession, CombatAction  # noqa: F401
            from app.models.economy import Trade, Auction, NPCMerchant  # noqa: F401
        except ImportError:
            # Models not created yet
            pass

        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db_connection():
    """
    Close database connection pool.
    This should be called during application shutdown.
    """
    await engine.dispose()
    logger.info("Database connection pool closed")


# Health check function
async def check_database_health() -> bool:
    """
    Check if database connection is healthy.

    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
