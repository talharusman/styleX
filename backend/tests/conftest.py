"""
Pytest Configuration and Fixtures

Shared fixtures for all tests.
"""

import os

# Tests must never touch the development database
os.environ["DATABASE_NAME"] = "stylex_test"
os.environ["ENVIRONMENT"] = "development"

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient

# Import the app
from app.main import app
from app.config import settings
from app.auth.jwt_handler import create_access_token


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def test_client() -> Generator:
    """Synchronous test client"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Async test client for async tests"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers() -> dict:
    """Get authentication headers for protected routes"""
    token = create_access_token({
        "user_id": "test_user_123",
        "email": "test@example.com",
        "roles": ["user"]
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers() -> dict:
    """Get admin authentication headers"""
    token = create_access_token({
        "user_id": "admin_user_123",
        "email": "admin@example.com",
        "roles": ["admin", "user"]
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_skin_features() -> dict:
    """Sample skin features for testing"""
    return {
        "undertone": "warm",
        "skin_depth": "medium",
        "seasonal_type": "autumn",
        "lab_l": 65.0,
        "lab_a": 12.0,
        "lab_b": 18.0,
        "skin_rgb": [198, 166, 145],
        "skin_hex": "#C6A691",
        "confidence": 0.92
    }


@pytest.fixture
def sample_cloth_features() -> dict:
    """Sample clothing features for testing"""
    return {
        "cloth_id": "test_001",
        "dominant_color_rgb": [70, 130, 180],
        "dominant_color_name": "steel blue",
        "color_hex": "#4682B4",
        "color_palette": [],
        "category": "top",
        "gender": "unisex",
        "style": "casual",
        "design": "solid",
        "fabric": "cotton",
        "weather": "all_season",
        "formality_level": 4,
        "confidence": 0.85
    }


@pytest.fixture
def sample_user_profile() -> dict:
    """Sample user profile for testing"""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "body_type": "athletic",
        "skin_tone": "warm",
        "style_preference": "casual",
        "gender": "unisex"
    }


@pytest.fixture
def sample_base64_image() -> str:
    """Sample 1x1 pixel image in base64 for testing"""
    # 1x1 red pixel PNG
    return (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIA"
        "K/X+FAAAAABJRU5ErkJggg=="
    )


@pytest.fixture
def mock_weather_data() -> dict:
    """Mock weather data for testing"""
    return {
        "location": "London",
        "temperature": 22.0,
        "feels_like": 21.0,
        "condition": "sunny",
        "description": "clear sky",
        "humidity": 45,
        "wind_speed": 5.5,
        "icon": "01d"
    }


@pytest.fixture
def mock_calendar_event() -> dict:
    """Mock calendar event for testing"""
    return {
        "id": "event_123",
        "title": "Business Meeting",
        "start_time": "2026-01-25T10:00:00",
        "end_time": "2026-01-25T11:00:00",
        "location": "Office",
        "description": "Quarterly review"
    }


# Test settings override
@pytest.fixture(autouse=True)
def override_settings():
    """Override settings for testing"""
    original_debug = settings.DEBUG
    original_env = settings.ENVIRONMENT
    
    settings.DEBUG = True
    settings.ENVIRONMENT = "testing"
    
    yield
    
    settings.DEBUG = original_debug
    settings.ENVIRONMENT = original_env
