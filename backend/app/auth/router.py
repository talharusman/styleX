"""
Authentication Router

API endpoints for user authentication with MongoDB backend.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import logging
import secrets
from datetime import datetime, timedelta

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
from app.database import (
    user_repository,
    get_user_repository,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)


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
    repo = get_user_repository()
    
    # Check if user exists
    existing_user = await repo.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create user
    user = await repo.create_user(
        email=request.email,
        password=request.password,
        name=request.name
    )
    
    logger.info(f"User registered: {request.email}")
    
    return AuthResponse(
        success=True,
        message="Registration successful",
        user=UserAuth(
            user_id=str(user.id),
            email=user.email,
            name=user.name,
            roles=user.roles
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
    repo = get_user_repository()
    
    # Authenticate user
    user = await repo.authenticate_user(request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    token_data = {
        "user_id": str(user.id),
        "email": user.email,
        "roles": user.roles
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    # Store refresh token in session
    await repo.create_session(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    # Update last login
    await repo.update_last_login(user.id)
    
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
    repo = get_user_repository()
    
    try:
        token_data = verify_token(request.refresh_token)
        
        if token_data.token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Verify session exists and is active
        session = await repo.get_session_by_token(request.refresh_token)
        if not session:
            # A correctly signed refresh token with no active session was already
            # rotated or revoked: treat as token theft/reuse and end all sessions.
            await repo.invalidate_all_user_sessions(token_data.user_id)
            logger.warning(f"Refresh token reuse detected for user {token_data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Check if token is expired
        if session.expires_at < datetime.utcnow():
            await repo.invalidate_session(request.refresh_token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        # Create new tokens
        new_token_data = {
            "user_id": token_data.user_id,
            "email": token_data.email,
            "roles": token_data.roles
        }
        
        access_token = create_access_token(new_token_data)
        new_refresh_token = create_refresh_token(new_token_data)
        
        # Invalidate old session and create new one
        await repo.invalidate_session(request.refresh_token)
        await repo.create_session(
            user_id=token_data.user_id,
            refresh_token=new_refresh_token,
            expires_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        return TokenResponse(
            success=True,
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
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
    Logout user and revoke all refresh tokens.
    
    Requires valid access token in Authorization header.
    """
    repo = get_user_repository()
    
    # Invalidate all user sessions
    count = await repo.invalidate_all_user_sessions(user.user_id)
    
    logger.info(f"User logged out: {user.user_id}, invalidated {count} sessions")
    
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
    repo = get_user_repository()
    
    # Get fresh user data from database
    db_user = await repo.get_user_by_id(user.user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return AuthResponse(
        success=True,
        message="User retrieved successfully",
        user=UserAuth(
            user_id=str(db_user.id),
            email=db_user.email,
            name=db_user.name,
            roles=db_user.roles,
            onboarding_completed=db_user.onboarding_completed
        )
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
    repo = get_user_repository()
    
    # Get user from database
    db_user = await repo.get_user_by_id(user.user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(request.current_password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    new_hash = hash_password(request.new_password)
    await repo.update_user(user.user_id, password_hash=new_hash)
    
    # Invalidate all sessions (force re-login)
    await repo.invalidate_all_user_sessions(user.user_id)
    
    logger.info(f"Password changed for user: {user.user_id}")
    
    return AuthResponse(
        success=True,
        message="Password changed successfully. Please login again."
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
    repo = get_user_repository()
    
    # Check if user exists
    user = await repo.get_user_by_email(request.email)
    
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
    from app.database import check_database_health
    
    db_health = await check_database_health()
    
    return {
        "status": "healthy" if db_health.get("status") == "healthy" else "degraded",
        "service": "auth",
        "database": db_health
    }

