"""
Simplified tests for configuration.

Tests basic configuration loading and validation.
"""

import pytest
import os
from unittest.mock import patch

from app.core.config import Settings, settings
from app.core.database import get_session


class TestSettings:
    """Test configuration settings."""
    
    def test_default_settings(self):
        """Test default configuration values."""
        test_settings = Settings()
        
        assert test_settings.app_name == "Text RPG API"
        assert test_settings.app_version == "1.0.0"
        assert test_settings.debug is False
        assert isinstance(test_settings.secret_key, str)
        assert len(test_settings.secret_key) > 0
        assert test_settings.access_token_expire_minutes > 0
        assert test_settings.database_pool_size > 0
        assert test_settings.max_characters_per_user == 5
    
    def test_database_url_format(self):
        """Test that database URL has correct format."""
        test_settings = Settings()
        
        assert test_settings.database_url.startswith("postgresql+asyncpg://")
        assert "@" in test_settings.database_url
        assert "/" in test_settings.database_url
    
    def test_environment_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            "APP_NAME": "Test Project",
            "DEBUG": "true",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "60"
        }):
            test_settings = Settings()
            
            assert test_settings.app_name == "Test Project"
            assert test_settings.debug is True
            assert test_settings.access_token_expire_minutes == 60
    
    def test_game_settings(self):
        """Test game-specific settings."""
        test_settings = Settings()
        
        assert test_settings.max_characters_per_user > 0
        assert test_settings.starting_health > 0
        assert test_settings.starting_mana >= 0
        assert test_settings.starting_level >= 1
        assert test_settings.starting_gold >= 0
    
    def test_global_settings_instance(self):
        """Test that global settings instance exists."""
        assert settings is not None
        assert isinstance(settings, Settings)
        assert settings.app_name == "Text RPG API" 