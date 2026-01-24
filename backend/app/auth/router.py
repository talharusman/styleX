"""
Authentication Router

API endpoints for user authentication.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import logging
import hashlib
import secrets

from .schemas import (
    LoginRequest, RegisterRequest, RefreshTokenRequest,
    TokenResponse, AuthResponse, UserAuth,
    PasswordResetRequest, PasswordChangeRequest
)
from .jwt_handler import (
    create_access_token, create_refresh_token,
    verify_token, get_current_user
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)

# In-memory user store (replace with database in production)
_users_db: dict = {}
_refresh_tokens: dict = {}


def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = settings.SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user"
)
async def register(request: RegisterRequest) -> AuthResponse:
    """
    Register a new user account.
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **name**: User's display name
    """
    # Check if user exists
    if request.email in _users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    user_id = f"user_{secrets.token_hex(8)}"
    _users_db[request.email] = {
        "user_id": user_id,
        "email": request.email,
        "name": request.name,
        "password_hash": hash_password(request.password),
        "roles": ["user"],
        "onboarding_complete": False
    }
    
    logger.info(f"User registered: {request.email}")
    
    return AuthResponse(
        success=True,
        message="Registration successful",
        user=UserAuth(
            user_id=user_id,
            email=request.email,
            name=request.name,
            roles=["user"]
        )
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login"
)
async def login(request: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.
    
    - **email**: Registered email address
    - **password**: User's password
    
    Returns access and refresh tokens.
    """
    # Find user
    user = _users_db.get(request.email)
    
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    token_data = {
        "user_id": user["user_id"],
        "email": user["email"],
        "roles": user["roles"]
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Store refresh token
    _refresh_tokens[user["user_id"]] = refresh_token
    
    logger.info(f"User logged in: {request.email}")
    
    return TokenResponse(
        success=True,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token"
)
async def refresh_token(request: RefreshTokenRequest) -> TokenResponse:
    """
    Get new access token using refresh token.
    
    - **refresh_token**: Valid refresh token from login
    """
    try:
        token_data = verify_token(request.refresh_token)
        
        if token_data.token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Verify refresh token is still valid
        stored_token = _refresh_tokens.get(token_data.user_id)
        if stored_token != request.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Create new tokens
        new_token_data = {
            "user_id": token_data.user_id,
            "email": token_data.email,
            "roles": token_data.roles
        }
        
        access_token = create_access_token(new_token_data)
        refresh_token = create_refresh_token(new_token_data)
        
        # Update stored refresh token
        _refresh_tokens[token_data.user_id] = refresh_token
        
        return TokenResponse(
            success=True,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post(
    "/logout",
    response_model=AuthResponse,
    summary="User logout"
)
async def logout(user: UserAuth = Depends(get_current_user)) -> AuthResponse:
    """
    Logout user and revoke refresh token.
    
    Requires valid access token in Authorization header.
    """
    # Revoke refresh token
    if user.user_id in _refresh_tokens:
        del _refresh_tokens[user.user_id]
    
    logger.info(f"User logged out: {user.user_id}")
    
    return AuthResponse(
        success=True,
        message="Logged out successfully"
    )


@router.get(
    "/me",
    response_model=AuthResponse,
    summary="Get current user"
)
async def get_me(user: UserAuth = Depends(get_current_user)) -> AuthResponse:
    """
    Get current authenticated user's information.
    
    Requires valid access token in Authorization header.
    """
    return AuthResponse(
        success=True,
        message="User retrieved successfully",
        user=user
    )


@router.post(
    "/password/change",
    response_model=AuthResponse,
    summary="Change password"
)
async def change_password(
    request: PasswordChangeRequest,
    user: UserAuth = Depends(get_current_user)
) -> AuthResponse:
    """
    Change user's password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters)
    """
    # Find user in database
    user_data = None
    for email, data in _users_db.items():
        if data["user_id"] == user.user_id:
            user_data = data
            break
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(request.current_password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    user_data["password_hash"] = hash_password(request.new_password)
    
    logger.info(f"Password changed for user: {user.user_id}")
    
    return AuthResponse(
        success=True,
        message="Password changed successfully"
    )


@router.post(
    "/password/reset",
    response_model=AuthResponse,
    summary="Request password reset"
)
async def request_password_reset(request: PasswordResetRequest) -> AuthResponse:
    """
    Request password reset email.
    
    - **email**: Registered email address
    
    Note: In production, this would send an email with a reset link.
    """
    # Check if user exists
    user = _users_db.get(request.email)
    
    # Always return success to prevent email enumeration
    if user:
        # In production: Generate reset token and send email
        logger.info(f"Password reset requested for: {request.email}")
    
    return AuthResponse(
        success=True,
        message="If the email exists, a reset link has been sent"
    )


@router.get(
    "/health",
    summary="Auth service health check"
)
async def health_check() -> dict:
    """Check auth service health"""
    return {
        "status": "healthy",
        "service": "auth",
        "users_count": len(_users_db)
    }
