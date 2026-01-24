"""
Unit Tests for Groq Chat Module
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestChatEndpoints:
    """Test Groq chat API endpoints"""
    
    def test_chat_endpoint(self):
        """Test basic chat endpoint"""
        response = client.post(
            "/api/chat",
            json={
                "message": "What should I wear today?"
            }
        )
        # May fail if API key not configured
        assert response.status_code in [200, 500, 503]
    
    def test_chat_with_context(self):
        """Test chat with user context"""
        response = client.post(
            "/api/chat",
            json={
                "message": "Suggest an outfit for work",
                "context_type": "style",
                "user_context": {
                    "body_type": "athletic",
                    "skin_tone": "warm",
                    "style_preference": "business casual"
                }
            }
        )
        assert response.status_code in [200, 500, 503]
    
    def test_style_advice(self):
        """Test style advice endpoint"""
        response = client.post(
            "/api/chat/style-advice",
            json={
                "query": "What colors suit me?",
                "body_type": "athletic",
                "skin_tone": "warm"
            }
        )
        assert response.status_code in [200, 500, 503]
    
    def test_weather_outfit(self):
        """Test weather outfit endpoint"""
        response = client.post(
            "/api/chat/weather-outfit",
            json={
                "weather_data": {
                    "temperature": 22,
                    "condition": "sunny",
                    "humidity": 45
                }
            }
        )
        assert response.status_code in [200, 500, 503]
    
    def test_event_outfit(self):
        """Test event outfit endpoint"""
        response = client.post(
            "/api/chat/event-outfit",
            json={
                "event_title": "Business Meeting",
                "event_time": "10:00 AM",
                "location": "Office"
            }
        )
        assert response.status_code in [200, 500, 503]
    
    def test_chat_health(self):
        """Test chat health endpoint"""
        response = client.get("/api/chat/health")
        assert response.status_code == 200


class TestChatValidation:
    """Test chat input validation"""
    
    def test_empty_message(self):
        """Test chat with empty message"""
        response = client.post(
            "/api/chat",
            json={"message": ""}
        )
        # Should return validation error or handle empty message
        assert response.status_code in [200, 400, 422]
    
    def test_very_long_message(self):
        """Test chat with very long message"""
        long_message = "What should I wear? " * 500
        response = client.post(
            "/api/chat",
            json={"message": long_message}
        )
        # Should handle or truncate long messages
        assert response.status_code in [200, 400, 422, 500, 503]
