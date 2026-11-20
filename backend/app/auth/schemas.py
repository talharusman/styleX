"""
Authentication Schemas

Pydantic models for authentication requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime


class UserAuth(BaseModel):
    """User authentication data"""
    user_id: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    roles: List[str] = Field(default_factory=lambda: ["user"])
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "email": "user@example.com",
                "name": "John Doe",
                "roles": ["user"]
            }
        }


class TokenData(BaseModel):
    """JWT Token payload data"""
    user_id: str
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    exp: Optional[datetime] = None
    token_type: str = "access"


class TokenResponse(BaseModel):
    """Token response for login/token endpoints"""
    success: bool = True
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiration in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str = Field(min_length=6)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


def validate_password_strength(value: str) -> str:
    """Require 8-128 chars with at least one letter and one digit."""
    if len(value) > 128:
        raise ValueError("Password must be at most 128 characters")
    if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one letter and one number")
    return value


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2, max_length=100)

    @field_validator("password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123",
                "name": "John Doe"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def _password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class AuthResponse(BaseModel):
    """Generic auth response"""
    success: bool
    message: str
    user: Optional[UserAuth] = None
