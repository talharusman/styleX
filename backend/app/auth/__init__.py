"""
Authentication Module

JWT authentication for protected routes.
Google OAuth is handled separately in the calendar module.
"""

from .jwt_handler import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    get_current_user_optional
)
from .schemas import TokenResponse, TokenData, UserAuth
from .router import router

__all__ = [
    "router",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",
    "get_current_user_optional",
    "TokenResponse",
    "TokenData",
    "UserAuth"
]
