"""
StyleX API - Main Application Entry Point

Complete backend for personalized AI fashion assistant.
"""

import time
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.common.logging_config import setup_logging
from app.common.exceptions import register_exception_handlers
from app.common.cache import get_cache, start_cache_cleanup_task
from app.database.connection import (
    connect_to_database,
    disconnect_from_database,
    check_database_health
)

# ========================================
# Router Imports
# ========================================
from app.auth.router import router as auth_router
from app.groq_chat.router import router as groq_chat_router
from app.weather.router import router as weather_router
from app.calendar.router import router as calendar_router
from app.onboarding.router import router as onboarding_router
from app.dashboard.router import router as dashboard_router
from app.profile.router import router as profile_router
from app.settings.router import router as settings_router
from app.face_analysis.router import router as face_analysis_router
from app.cloth_analysis.router import router as cloth_analysis_router
from app.recommendation.router import router as recommendation_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # ========================================
    # Startup
    # ========================================
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_file=settings.LOG_FILE if settings.ENVIRONMENT != "development" else None,
        structured=settings.ENVIRONMENT == "production"
    )
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Connect to MongoDB
    try:
        await connect_to_database()
        logger.info("✅ MongoDB database connected")
    except Exception as e:
        logger.error(f"❌ {e}")
        raise
    
    # Start cache cleanup background task
    if settings.CACHE_ENABLED:
        asyncio.create_task(start_cache_cleanup_task())
        logger.info("Cache cleanup task started")
    
    # Initialize services that need startup
    try:
        from app.dashboard.service import get_dashboard_service
        from app.weather.service import get_weather_service
        from app.calendar.service import get_calendar_service
        
        dashboard = get_dashboard_service()
        dashboard.set_services(
            weather_service=get_weather_service(),
            calendar_service=get_calendar_service()
        )
        logger.info("Dashboard service connected to weather and calendar")
    except Exception as e:
        logger.warning(f"Service initialization warning: {e}")
    
    yield
    
    # ========================================
    # Shutdown
    # ========================================
    logger.info("Shutting down application...")
    
    # Clear cache on shutdown
    cache = get_cache()
    await cache.clear()
    
    # Disconnect from MongoDB
    await disconnect_from_database()
    logger.info("✅ MongoDB connection closed")
    
    logger.info("Application shutdown complete")


# ========================================
# Create FastAPI Application
# ========================================
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    StyleX API - AI-Powered Personal Fashion Assistant
    
    Features:
    - **Face Analysis**: Skin tone detection and color recommendations
    - **Cloth Analysis**: Clothing feature extraction (color, style, category)
    - **Recommendations**: AI-powered outfit matching
    - **Groq Chat**: Natural language styling advice
    - **Weather Integration**: Weather-based outfit suggestions
    - **Google Calendar**: Event-based outfit planning
    - **Virtual Try-On**: Visualize outfits (coming soon)
    
    All endpoints return consistent error responses:
    ```json
    { "success": false, "message": "...", "code": 400 }
    ```
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# ========================================
# Middleware
# ========================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list if settings.ENVIRONMENT == "production" else ["*"],
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Add request timing to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = (time.time() - start_time) * 1000
    
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration, 2),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    return response


# ========================================
# Register Exception Handlers
# ========================================
register_exception_handlers(app)


# ========================================
# Include Routers
# ========================================

# Authentication
app.include_router(auth_router)

# AI Chat
app.include_router(groq_chat_router)

# Weather
app.include_router(weather_router)

# Google Calendar
app.include_router(calendar_router)

# Onboarding
app.include_router(onboarding_router)

# Dashboard
app.include_router(dashboard_router)

# Profile
app.include_router(profile_router)

# Settings  
app.include_router(settings_router)

# Face Analysis
app.include_router(face_analysis_router)

# Cloth Analysis
app.include_router(cloth_analysis_router)

# Recommendations
app.include_router(recommendation_router)


# ========================================
# Root Endpoints
# ========================================

@app.get("/", tags=["Root"])
async def root():
    """Welcome endpoint with API information"""
    return {
        "success": True,
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Root"])
async def health():
    """Health check endpoint for monitoring"""
    cache = get_cache()
    cache_stats = cache.get_stats()
    
    # Check database health
    db_health = await check_database_health()
    
    return {
        "success": True,
        "status": "healthy" if db_health.get("status") == "healthy" else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_health,
        "cache": cache_stats,
        "services": {
            "auth": "operational",
            "groq_chat": "operational" if settings.GROQ_API_KEY else "unconfigured",
            "weather": "operational" if settings.OPENWEATHER_API_KEY else "unconfigured",
            "calendar": "operational" if settings.GOOGLE_CLIENT_ID else "unconfigured",
            "face_analysis": "operational",
            "cloth_analysis": "operational",
            "recommendation": "operational"
        }
    }


@app.get("/cache/stats", tags=["Root"])
async def cache_stats():
    """Get cache statistics"""
    cache = get_cache()
    return {
        "success": True,
        "cache": cache.get_stats()
    }


@app.post("/cache/clear", tags=["Root"])
async def clear_cache(pattern: str = None):
    """Clear cache entries (admin only in production)"""
    cache = get_cache()
    cleared = await cache.clear(pattern)
    return {
        "success": True,
        "message": f"Cleared {cleared} cache entries"
    }
