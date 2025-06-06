"""
Tests for database connection and session management.

Validates database engine creation, session handling, and health checks.
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import (
    get_engine, get_session, create_db_and_tables, 
    close_db_connection, check_database_health
)


class TestDatabaseEngine:
    """Test database engine configuration."""
    
    def test_get_engine_returns_engine(self):
        """Test that get_engine returns the database engine."""
        engine = get_engine()
        assert isinstance(engine, AsyncEngine)
        assert engine is not None
    
    def test_engine_exists_and_has_correct_type(self):
        """Test that the database engine exists and is properly configured."""
        from app.core.database import engine
        from sqlalchemy.ext.asyncio import AsyncEngine
        
        # Verify engine exists and is correct type
        assert engine is not None
        assert isinstance(engine, AsyncEngine)
        assert hasattr(engine, 'url')
        
    def test_engine_url_configuration(self):
        """Test that engine URL is configured correctly."""
        from app.core.database import engine
        from app.core.config import settings
        
        # Verify the engine URL matches settings
        assert str(engine.url).startswith(settings.database_url.split('://')[0])
        # Should be either sqlite or postgresql URL
        assert any(db_type in str(engine.url) for db_type in ['sqlite', 'postgresql'])


class TestDatabaseSession:
    """Test database session management."""
    
    async def test_get_session_success(self):
        """Test successful session creation and cleanup."""
        async for session in get_session():
            assert isinstance(session, AsyncSession)
            assert session is not None
    
    async def test_get_session_error_handling(self):
        """Test session error handling and rollback."""
        with patch('app.core.database.AsyncSessionLocal') as mock_session_class:
            # Create mock session that raises an error
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session_class.return_value = mock_session
            
            # Mock an exception during session use
            with patch('app.core.database.logger') as mock_logger:
                # Create a session generator
                session_gen = get_session()
                session = await session_gen.__anext__()
                
                # Simulate an exception
                try:
                    await session_gen.athrow(Exception("Test error"))
                except Exception:
                    pass
                
                # Verify rollback was called
                mock_session.rollback.assert_called_once()
                mock_logger.error.assert_called_once()


class TestDatabaseTables:
    """Test database table creation."""
    
    async def test_create_db_and_tables_success(self):
        """Test successful database table creation."""
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            
            with patch('app.core.database.SQLModel') as mock_sqlmodel:
                with patch('app.core.database.logger') as mock_logger:
                    await create_db_and_tables()
                    
                    # Verify connection and table creation
                    mock_engine.begin.assert_called_once()
                    mock_conn.run_sync.assert_called_once_with(mock_sqlmodel.metadata.create_all)
                    mock_logger.info.assert_called_with("Database tables created successfully")
    
    async def test_create_db_and_tables_with_import_error(self):
        """Test table creation when model imports fail."""
        with patch('app.core.database.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            
            # Mock import error for models
            with patch('builtins.__import__', side_effect=ImportError("Models not found")):
                with patch('app.core.database.SQLModel') as mock_sqlmodel:
                    with patch('app.core.database.logger') as mock_logger:
                        await create_db_and_tables()
                        
                        # Should still create tables even with import errors
                        mock_conn.run_sync.assert_called_once_with(mock_sqlmodel.metadata.create_all)
                        mock_logger.info.assert_called_with("Database tables created successfully")


class TestDatabaseCleanup:
    """Test database cleanup operations."""
    
    async def test_close_db_connection(self):
        """Test database connection pool closure."""
        with patch('app.core.database.engine') as mock_engine:
            mock_engine.dispose = AsyncMock()
            with patch('app.core.database.logger') as mock_logger:
                await close_db_connection()
                
                mock_engine.dispose.assert_called_once()
                mock_logger.info.assert_called_with("Database connection pool closed")


class TestDatabaseHealth:
    """Test database health check functionality."""
    
    async def test_check_database_health_success(self):
        """Test successful database health check."""
        with patch('app.core.database.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session_class.return_value.__aexit__.return_value = None
            
            result = await check_database_health()
            
            assert result is True
            mock_session.execute.assert_called_once_with("SELECT 1")
    
    async def test_check_database_health_failure(self):
        """Test database health check failure."""
        with patch('app.core.database.AsyncSessionLocal') as mock_session_class:
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("Connection failed")
            mock_session_class.return_value.__aenter__.return_value = mock_session
            mock_session_class.return_value.__aexit__.return_value = None
            
            with patch('app.core.database.logger') as mock_logger:
                result = await check_database_health()
                
                assert result is False
                mock_logger.error.assert_called_once()
                assert "Database health check failed" in str(mock_logger.error.call_args) 