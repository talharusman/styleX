"""
Google OAuth Handler - Handles OAuth 2.0 authentication flow
"""

import os
import secrets
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode
import httpx

logger = logging.getLogger(__name__)


class GoogleOAuth:
    """Handles Google OAuth 2.0 authentication flow"""
    
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    REVOKE_URL = "https://oauth2.googleapis.com/revoke"
    
    # Required scopes for calendar access
    SCOPES = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ):
        """
        Initialize Google OAuth handler
        
        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            redirect_uri: OAuth callback URL
        """
        self.client_id = client_id or os.getenv("GOOGLE_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("GOOGLE_CLIENT_SECRET", "")
        self.redirect_uri = redirect_uri or os.getenv(
            "GOOGLE_REDIRECT_URI",
            "http://localhost:8000/api/calendar/auth/callback"
        )
        
        # In-memory state storage (use Redis/DB in production)
        self._state_storage: Dict[str, Dict[str, Any]] = {}
        
        if not self.client_id or not self.client_secret:
            logger.warning(
                "Google OAuth credentials not configured. "
                "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
            )
    
    def generate_auth_url(
        self,
        user_id: Optional[str] = None,
        additional_scopes: Optional[list] = None
    ) -> Dict[str, str]:
        """
        Generate OAuth authorization URL
        
        Args:
            user_id: Optional user ID to associate with the OAuth flow
            additional_scopes: Optional additional scopes to request
            
        Returns:
            Dict with auth_url and state token
        """
        state = secrets.token_urlsafe(32)
        
        # Store state for validation
        self._state_storage[state] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "redirect_uri": self.redirect_uri
        }
        
        scopes = self.SCOPES.copy()
        if additional_scopes:
            scopes.extend(additional_scopes)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent"  # Force consent to get refresh token
        }
        
        auth_url = f"{self.AUTHORIZATION_URL}?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    async def exchange_code(
        self,
        code: str,
        state: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens
        
        Args:
            code: Authorization code from callback
            state: State token for validation
            
        Returns:
            Dict with access_token, refresh_token, and user info
        """
        # Validate state
        if state not in self._state_storage:
            raise ValueError("Invalid state token")
        
        stored_state = self._state_storage.pop(state)
        
        # Check state expiration (10 minutes)
        if datetime.utcnow() - stored_state["created_at"] > timedelta(minutes=10):
            raise ValueError("State token expired")
        
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri
                }
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(f"Token exchange failed: {error_data.get('error_description', 'Unknown error')}")
            
            tokens = response.json()
        
        # Get user info
        user_info = await self.get_user_info(tokens["access_token"])
        
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens["expires_in"],
            "token_type": tokens["token_type"],
            "scope": tokens.get("scope", ""),
            "user_info": user_info,
            "stored_user_id": stored_state.get("user_id")
        }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an expired access token
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            New token data
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code != 200:
                error_data = response.json()
                raise ValueError(f"Token refresh failed: {error_data.get('error_description', 'Unknown error')}")
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information using access token
        
        Args:
            access_token: Valid access token
            
        Returns:
            User information dict
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise ValueError("Failed to get user info")
            
            return response.json()
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke an access or refresh token
        
        Args:
            token: Token to revoke
            
        Returns:
            True if successful
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.REVOKE_URL,
                params={"token": token}
            )
            
            return response.status_code == 200
    
    def is_configured(self) -> bool:
        """Check if OAuth is properly configured"""
        return bool(self.client_id and self.client_secret)
    
    def clean_expired_states(self):
        """Clean up expired state tokens"""
        now = datetime.utcnow()
        expired = [
            state for state, data in self._state_storage.items()
            if now - data["created_at"] > timedelta(minutes=10)
        ]
        for state in expired:
            del self._state_storage[state]


# Singleton instance
_oauth_instance: Optional[GoogleOAuth] = None


def get_google_oauth() -> GoogleOAuth:
    """Get or create the Google OAuth singleton"""
    global _oauth_instance
    if _oauth_instance is None:
        _oauth_instance = GoogleOAuth()
    return _oauth_instance
