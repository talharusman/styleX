"""
MongoDB Database Connection Setup with Beanie ODM.

Provides async MongoDB connection and model initialization for StyleX application.
Uses Motor as the async MongoDB driver and Beanie as the ODM.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import settings

logger = logging.getLogger(__name__)


def _redact(url: str) -> str:
    """Hide credentials in a MongoDB URL before logging/raising."""
    if "@" in url:
        scheme, rest = url.split("://", 1) if "://" in url else ("mongodb", url)
        return f"{scheme}://***@{rest.rsplit('@', 1)[1]}"
    return url

# Global database client and database instances
_client: Optional[AsyncIOMotorClient] = None
_database = None


async def connect_to_database() -> None:
    """
    Initialize MongoDB connection and Beanie ODM.
    
    Should be called during application startup.
    """
    global _client, _database
    
    try:
        logger.info(f"Connecting to MongoDB at {_redact(settings.DATABASE_URL)}...")
        
        # Create MongoDB client with connection pooling
        _client = AsyncIOMotorClient(
            settings.DATABASE_URL,
            minPoolSize=settings.MONGO_MIN_POOL_SIZE,
            maxPoolSize=settings.MONGO_MAX_POOL_SIZE,
            maxIdleTimeMS=settings.MONGO_MAX_IDLE_TIME_MS,
            serverSelectionTimeoutMS=settings.MONGO_SERVER_SELECTION_TIMEOUT_MS,
        )
        
        # Test connection
        await _client.admin.command('ping')
        logger.info("✅ MongoDB connection established successfully")
        
        # Get database
        _database = _client[settings.DATABASE_NAME]
        
        # Import models here to avoid circular imports
        from .models import (
            User,
            UserProfile,
            UserSettings,
            UserSession,
            ClothingItem,
            AnalysisResult,
            OutfitRecommendation,
            CalendarEvent,
            ChatMessage,
            OnboardingProgress,
        )
        
        # Initialize Beanie with document models
        await init_beanie(
            database=_database,
            document_models=[
                User,
                UserProfile,
                UserSettings,
                UserSession,
                ClothingItem,
                AnalysisResult,
                OutfitRecommendation,
                CalendarEvent,
                ChatMessage,
                OnboardingProgress,
            ]
        )
        logger.info("✅ Beanie ODM initialized with all document models")
        
    except (ServerSelectionTimeoutError, ConnectionFailure) as e:
        if _client:
            _client.close()
            _client = None
        raise RuntimeError(
            f"Cannot reach MongoDB at {_redact(settings.DATABASE_URL)}. "
            "StyleX requires a running MongoDB. Start one with "
            "`docker compose up -d mongo` (or install MongoDB locally) and check "
            "DATABASE_URL in backend/.env. "
            f"Underlying error: {type(e).__name__}"
        ) from e
    except Exception as e:
        logger.error(f"❌ Failed to initialise database: {e}")
        raise


async def disconnect_from_database() -> None:
    """
    Close MongoDB connection.
    
    Should be called during application shutdown.
    """
    global _client, _database
    
    if _client:
        _client.close()
        _client = None
        _database = None
        logger.info("📪 MongoDB connection closed")


def get_database():
    """
    Get the current database instance.
    
    Returns:
        The MongoDB database instance.
        
    Raises:
        RuntimeError: If database is not connected.
    """
    if _database is None:
        raise RuntimeError("Database not connected. Call connect_to_database() first.")
    return _database


def get_client() -> AsyncIOMotorClient:
    """
    Get the MongoDB client instance.
    
    Returns:
        The AsyncIOMotorClient instance.
        
    Raises:
        RuntimeError: If client is not connected.
    """
    if _client is None:
        raise RuntimeError("Database not connected. Call connect_to_database() first.")
    return _client


async def check_database_health() -> dict:
    """
    Check database connection health.
    
    Returns:
        Dict with health status information.
    """
    try:
        if _client is None:
            return {"status": "disconnected", "error": "No connection"}
        
        # Ping database
        await _client.admin.command('ping')
        
        # Get server info
        server_info = await _client.server_info()
        
        return {
            "status": "healthy",
            "mongodb_version": server_info.get("version", "unknown"),
            "database": settings.DATABASE_NAME,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
