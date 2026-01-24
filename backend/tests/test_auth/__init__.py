"""
Unit Tests for Authentication Module
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth.jwt_handler import create_access_token, create_refresh_token, verify_token


client = TestClient(app)


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_register_success(self):
        """Test successful user registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["user"]["email"] == "newuser@example.com"
    
    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123",
                "name": "User One"
            }
        )
        
        # Duplicate registration
        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "password456",
                "name": "User Two"
            }
        )
        assert response.status_code == 409
    
    def test_login_success(self):
        """Test successful login"""
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "email": "logintest@example.com",
                "password": "testpassword123",
                "name": "Login Test"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_get_current_user(self):
        """Test getting current user with valid token"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "email": "currentuser@example.com",
                "password": "password123",
                "name": "Current User"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "currentuser@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["email"] == "currentuser@example.com"
    
    def test_get_current_user_no_token(self):
        """Test getting current user without token"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
    
    def test_refresh_token(self):
        """Test token refresh"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "email": "refreshtest@example.com",
                "password": "password123",
                "name": "Refresh Test"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "refreshtest@example.com",
                "password": "password123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    def test_logout(self):
        """Test user logout"""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "email": "logouttest@example.com",
                "password": "password123",
                "name": "Logout Test"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "logouttest@example.com",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_health_check(self):
        """Test auth health endpoint"""
        response = client.get("/api/auth/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestJWTHandler:
    """Test JWT token handling"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        token = create_access_token({"user_id": "test123", "email": "test@example.com"})
        assert token is not None
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token = create_refresh_token({"user_id": "test123"})
        assert token is not None
        assert len(token) > 0
    
    def test_verify_valid_token(self):
        """Test verifying a valid token"""
        token = create_access_token({"user_id": "test123", "email": "test@example.com"})
        token_data = verify_token(token)
        assert token_data.user_id == "test123"
        assert token_data.email == "test@example.com"
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token"""
        with pytest.raises(Exception):
            verify_token("invalid_token")
