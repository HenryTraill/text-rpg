from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings and configuration.
    
    All settings can be overridden via environment variables.
    """
    
    # Application Settings
    app_name: str = "Text RPG API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database Settings
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/text_rpg"
    database_pool_size: int = 20
    database_max_overflow: int = 30
    database_pool_timeout: int = 30
    database_pool_recycle: int = 3600
    
    # Redis Settings
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 100
    
    # Authentication Settings
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # 15 minutes as per requirements
    refresh_token_expire_days: int = 7     # 7 days as per requirements
    
    # Security Settings
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    
    # Game Settings
    max_characters_per_user: int = 5
    default_starting_zone: str = "starter_town"
    starting_health: int = 100
    starting_mana: int = 50
    starting_experience: int = 0
    starting_level: int = 1
    starting_gold: int = 100
    
    # Performance Settings
    api_rate_limit: int = 100  # requests per minute
    websocket_max_connections: int = 1000
    chat_message_history_limit: int = 100
    
    # Spatial Settings
    world_size_x: float = 10000.0
    world_size_y: float = 10000.0
    proximity_search_radius: float = 100.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()