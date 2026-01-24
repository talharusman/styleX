"""
JWT Token Handler

Creates and verifies JWT tokens for authentication.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import logging

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from .schemas import TokenData, UserAuth

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data (must include 'user_id')
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "token_type": "access"
    })
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Payload data (must include 'user_id')
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "token_type": "refresh"
    })
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_token(token: str) -> TokenData:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData with decoded payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
        return TokenData(
            user_id=user_id,
            email=payload.get("email"),
            roles=payload.get("roles", []),
            token_type=payload.get("token_type", "access")
        )
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise credentials_exception


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UserAuth:
    """
    FastAPI dependency to get the current authenticated user.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: UserAuth = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token_data = verify_token(credentials.credentials)
    
    return UserAuth(
        user_id=token_data.user_id,
        email=token_data.email,
        roles=token_data.roles
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserAuth]:
    """
    FastAPI dependency to get the current user, or None if not authenticated.
    
    Use this for routes that work with or without authentication.
    """
    if credentials is None:
        return None
    
    try:
        token_data = verify_token(credentials.credentials)
        return UserAuth(
            user_id=token_data.user_id,
            email=token_data.email,
            roles=token_data.roles
        )
    except HTTPException:
        return None


def require_roles(*required_roles: str):
    """
    Dependency factory to require specific roles.
    
    Usage:
        @router.get("/admin")
        async def admin_route(user: UserAuth = Depends(require_roles("admin"))):
            return {"message": "Admin access granted"}
    """
    async def role_checker(
        user: UserAuth = Depends(get_current_user)
    ) -> UserAuth:
        if not any(role in user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    
    return role_checker
