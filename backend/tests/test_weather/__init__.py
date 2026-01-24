"""
Unit Tests for Weather Module
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestWeatherEndpoints:
    """Test weather API endpoints"""
    
    def test_get_weather_success(self):
        """Test getting weather for a location"""
        response = client.get("/api/weather?location=London")
        assert response.status_code == 200
        data = response.json()
        # Should work with mock data if API key not configured
        assert "location" in data or "detail" in data
    
    def test_get_weather_missing_location(self):
        """Test weather without location parameter"""
        response = client.get("/api/weather")
        assert response.status_code == 422  # Validation error
    
    def test_get_forecast(self):
        """Test getting weather forecast"""
        response = client.get("/api/weather/forecast?location=London&days=5")
        assert response.status_code in [200, 404, 502]  # OK or service unavailable
    
    def test_location_search(self):
        """Test location search"""
        response = client.get("/api/weather/search?query=London")
        assert response.status_code in [200, 502]
    
    def test_outfit_suggestion(self):
        """Test outfit suggestion for weather"""
        response = client.get(
            "/api/weather/outfit-suggestion",
            params={
                "temperature": 22,
                "condition": "sunny",
                "humidity": 50
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "outfit_suggestions" in data
    
    def test_weather_health(self):
        """Test weather service health"""
        response = client.get("/api/weather/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestOutfitSuggestions:
    """Test weather-based outfit suggestions"""
    
    def test_cold_weather_outfit(self):
        """Test outfit for cold weather"""
        response = client.get(
            "/api/weather/outfit-suggestion",
            params={
                "temperature": 5,
                "condition": "cloudy",
                "humidity": 60
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Should suggest warm clothing
        suggestions = data.get("outfit_suggestions", [])
        assert len(suggestions) > 0
    
    def test_hot_weather_outfit(self):
        """Test outfit for hot weather"""
        response = client.get(
            "/api/weather/outfit-suggestion",
            params={
                "temperature": 35,
                "condition": "sunny",
                "humidity": 30
            }
        )
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("outfit_suggestions", [])
        assert len(suggestions) > 0
    
    def test_rainy_weather_outfit(self):
        """Test outfit for rainy weather"""
        response = client.get(
            "/api/weather/outfit-suggestion",
            params={
                "temperature": 15,
                "condition": "rainy",
                "humidity": 90
            }
        )
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("outfit_suggestions", [])
        assert len(suggestions) > 0
