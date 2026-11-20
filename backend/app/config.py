"""
Application Configuration Settings

Centralized configuration management using pydantic-settings.
Environment variables are loaded from .env file.
"""

import os
from typing import Optional, List, Union
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ========================================
    # Application Settings
    # ========================================
    APP_NAME: str = "StyleX API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # ========================================
    # Server Settings
    # ========================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # ========================================
    # Security Settings
    # ========================================
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Settings - stored as string, parsed to list
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    CORS_ALLOW_CREDENTIALS: bool = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string to list"""
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # ========================================
    # Database Settings - MongoDB
    # ========================================
    DATABASE_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "stylex"
    DATABASE_ECHO: bool = False
    
    # MongoDB Connection Pool Settings
    MONGO_MIN_POOL_SIZE: int = 10
    MONGO_MAX_POOL_SIZE: int = 100
    MONGO_MAX_IDLE_TIME_MS: int = 30000
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = 5000  # fail fast if MongoDB is down
    
    # ========================================
    # API Keys - External Services
    # ========================================
    # Groq AI (LLM Chat)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # OpenWeatherMap
    OPENWEATHER_API_KEY: str = ""
    
    # Google OAuth (Calendar)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/calendar/auth/callback"
    
    # ========================================
    # Caching Settings
    # ========================================
    CACHE_ENABLED: bool = True
    CACHE_TTL_WEATHER: int = 600  # 10 minutes
    CACHE_TTL_FACE_ANALYSIS: int = 300  # 5 minutes
    CACHE_TTL_RECOMMENDATION: int = 300  # 5 minutes
    CACHE_TTL_DEFAULT: int = 300  # 5 minutes
    
    # ========================================
    # Logging Settings
    # ========================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None  # Set to "logs/stylex.log" in production
    
    # ========================================
    # Model Settings (AI/ML)
    # ========================================
    USE_GPU: bool = True
    USE_FP16: bool = True
    IMAGE_SIZE: int = 224
    USE_CLIP: bool = True
    MODEL_PATH: str = "models/"
    
    # ========================================
    # Rate Limiting
    # ========================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Convenience instance
settings = get_settings()
