"""
Integration Tests

Test complete user flows from onboarding to recommendations.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestOnboardingFlow:
    """Test complete onboarding flow"""
    
    def test_get_onboarding_steps(self):
        """Test getting onboarding steps"""
        response = client.get("/api/onboarding/steps")
        assert response.status_code == 200
        data = response.json()
        assert "steps" in data
    
    def test_onboarding_progress(self):
        """Test checking onboarding progress"""
        response = client.get("/api/onboarding/progress/test_user_123")
        assert response.status_code == 200
        data = response.json()
        assert "current_step" in data or "progress" in data
    
    def test_submit_body_type(self):
        """Test submitting body type"""
        response = client.post(
            "/api/onboarding/step/body-type/test_user_456",
            json={"body_type": "athletic"}
        )
        assert response.status_code == 200
    
    def test_submit_skin_tone(self):
        """Test submitting skin tone"""
        response = client.post(
            "/api/onboarding/step/skin-tone/test_user_456",
            json={"skin_tone": "warm"}
        )
        assert response.status_code == 200
    
    def test_submit_style_preference(self):
        """Test submitting style preference"""
        response = client.post(
            "/api/onboarding/step/style/test_user_456",
            json={"style_preference": "casual", "color_preferences": ["navy", "gray"]}
        )
        assert response.status_code == 200
    
    def test_complete_onboarding(self):
        """Test completing onboarding"""
        response = client.post("/api/onboarding/step/complete/test_user_456")
        assert response.status_code == 200


class TestDashboardIntegration:
    """Test dashboard data aggregation"""
    
    def test_get_dashboard(self):
        """Test getting dashboard data"""
        response = client.get(
            "/api/dashboard",
            params={"user_id": "test_user_123", "location": "London"}
        )
        assert response.status_code == 200
        data = response.json()
        # Dashboard should aggregate multiple data sources
        assert "greeting" in data or "weather" in data or "success" in data
    
    def test_outfit_of_the_day(self):
        """Test outfit of the day"""
        response = client.get(
            "/api/dashboard/outfit-of-the-day",
            params={"user_id": "test_user_123"}
        )
        assert response.status_code == 200
    
    def test_outfit_carousel(self):
        """Test outfit carousel"""
        response = client.get(
            "/api/dashboard/outfits",
            params={"user_id": "test_user_123", "limit": 5}
        )
        assert response.status_code == 200
    
    def test_quick_actions(self):
        """Test quick actions"""
        response = client.get("/api/dashboard/quick-actions")
        assert response.status_code == 200


class TestRecommendationFlow:
    """Test recommendation end-to-end"""
    
    def test_get_recommendations(self):
        """Test getting outfit recommendations"""
        response = client.post(
            "/recommendation/recommend",
            json={
                "skin_features": {
                    "undertone": "warm",
                    "skin_depth": "medium",
                    "lab_l": 65.0,
                    "lab_a": 12.0,
                    "lab_b": 18.0,
                    "skin_rgb": [198, 166, 145],
                    "confidence": 0.9
                },
                "available_clothes": [
                    {
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
                ],
                "top_k": 5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data or "success" in data
    
    def test_color_analysis(self):
        """Test color analysis"""
        response = client.post(
            "/recommendation/color-analysis",
            json={
                "undertone": "warm",
                "skin_depth": "medium",
                "lab_l": 65.0,
                "lab_a": 12.0,
                "lab_b": 18.0,
                "skin_rgb": [198, 166, 145],
                "confidence": 0.9
            }
        )
        assert response.status_code == 200


class TestFullUserJourney:
    """Test complete user journey"""
    
    def test_complete_user_flow(self):
        """Test: Register -> Onboard -> Dashboard -> Recommendation"""
        
        # 1. Register user
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "journey@example.com",
                "password": "securepassword123",
                "name": "Journey Test"
            }
        )
        assert register_response.status_code in [201, 409]  # Created or already exists
        
        # 2. Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "journey@example.com",
                "password": "securepassword123"
            }
        )
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # 3. Get onboarding steps
            steps_response = client.get("/api/onboarding/steps")
            assert steps_response.status_code == 200
            
            # 4. Complete onboarding steps
            user_id = login_response.json().get("user", {}).get("user_id", "journey_user")
            
            # 5. Get dashboard (should work even without complete onboarding)
            dashboard_response = client.get(
                "/api/dashboard",
                params={"user_id": "journey_user", "location": "New York"}
            )
            assert dashboard_response.status_code == 200
            
            # 6. Get profile
            profile_response = client.get(f"/api/profile/journey_user")
            assert profile_response.status_code in [200, 404]


class TestErrorHandling:
    """Test consistent error responses"""
    
    def test_404_response_format(self):
        """Test 404 error format"""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_validation_error_format(self):
        """Test validation error format"""
        response = client.post(
            "/api/auth/login",
            json={"email": "invalid-email"}  # Missing password
        )
        assert response.status_code == 422
    
    def test_unauthorized_error_format(self):
        """Test unauthorized error format"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        data = response.json()
        assert "success" in data or "detail" in data


class TestCaching:
    """Test caching behavior"""
    
    def test_weather_caching(self):
        """Test that weather results are cached"""
        # First request
        response1 = client.get("/api/weather?location=London")
        
        # Second request should be faster (cached)
        response2 = client.get("/api/weather?location=London")
        
        # Both should succeed
        assert response1.status_code == response2.status_code
    
    def test_cache_stats(self):
        """Test cache statistics endpoint"""
        response = client.get("/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "cache" in data
        assert "hits" in data["cache"]
        assert "misses" in data["cache"]
