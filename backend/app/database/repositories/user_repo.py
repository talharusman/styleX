"""
User Repository - MongoDB operations for User management.

Provides CRUD operations for User, UserProfile, UserSettings, and UserSession documents.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
from beanie import PydanticObjectId
from passlib.context import CryptContext

from app.database.models import (
    User, UserProfile, UserSettings, UserSession, OnboardingProgress
)

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


class UserRepository:
    """Repository for User CRUD operations."""
    
    # ==========================================
    # USER OPERATIONS
    # ==========================================
    
    async def create_user(
        self,
        email: str,
        password: str,
        name: str,
        **kwargs
    ) -> User:
        """
        Create a new user with associated profile and settings.
        
        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            name: User's display name
            **kwargs: Additional user fields
            
        Returns:
            Created User document
        """
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            **kwargs
        )
        await user.insert()
        
        # Create associated profile
        await self.create_user_profile(user.id)
        
        # Create associated settings
        await self.create_user_settings(user.id)
        
        # Create onboarding progress
        await self.create_onboarding_progress(user.id)
        
        logger.info(f"Created new user: {email}")
        return user
    
    async def get_user_by_id(self, user_id: str | PydanticObjectId) -> Optional[User]:
        """Get user by ID."""
        if isinstance(user_id, str):
            try:
                user_id = PydanticObjectId(user_id)
            except Exception:
                return None
        return await User.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return await User.find_one(User.email == email)
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google OAuth ID."""
        return await User.find_one(User.google_id == google_id)
    
    async def update_user(
        self,
        user_id: str | PydanticObjectId,
        **updates
    ) -> Optional[User]:
        """Update user fields."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        updates['updated_at'] = datetime.utcnow()
        await user.update({"$set": updates})
        return await self.get_user_by_id(user_id)
    
    async def update_last_login(self, user_id: str | PydanticObjectId) -> None:
        """Update user's last login timestamp."""
        user = await self.get_user_by_id(user_id)
        if user:
            await user.update({"$set": {"last_login": datetime.utcnow()}})
    
    async def delete_user(self, user_id: str | PydanticObjectId) -> bool:
        """Delete user and all associated data."""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        # Delete associated data
        await UserProfile.find(UserProfile.user_id == user_id).delete()
        await UserSettings.find(UserSettings.user_id == user_id).delete()
        await UserSession.find(UserSession.user_id == user_id).delete()
        await OnboardingProgress.find(OnboardingProgress.user_id == user_id).delete()
        
        # Delete user
        await user.delete()
        logger.info(f"Deleted user: {user_id}")
        return True
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Returns:
            User if authentication successful, None otherwise
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    # ==========================================
    # USER PROFILE OPERATIONS
    # ==========================================
    
    async def create_user_profile(self, user_id: PydanticObjectId) -> UserProfile:
        """Create initial user profile."""
        profile = UserProfile(user_id=user_id)
        await profile.insert()
        return profile
    
    async def get_user_profile(self, user_id: str | PydanticObjectId) -> Optional[UserProfile]:
        """Get user profile by user ID."""
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        return await UserProfile.find_one(UserProfile.user_id == user_id)
    
    async def update_user_profile(
        self,
        user_id: str | PydanticObjectId,
        **updates
    ) -> Optional[UserProfile]:
        """Update user profile fields."""
        profile = await self.get_user_profile(user_id)
        if not profile:
            return None
        
        updates['updated_at'] = datetime.utcnow()
        await profile.update({"$set": updates})
        return await self.get_user_profile(user_id)
    
    # ==========================================
    # USER SETTINGS OPERATIONS
    # ==========================================
    
    async def create_user_settings(self, user_id: PydanticObjectId) -> UserSettings:
        """Create initial user settings."""
        settings = UserSettings(user_id=user_id)
        await settings.insert()
        return settings
    
    async def get_user_settings(self, user_id: str | PydanticObjectId) -> Optional[UserSettings]:
        """Get user settings by user ID."""
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        return await UserSettings.find_one(UserSettings.user_id == user_id)
    
    async def update_user_settings(
        self,
        user_id: str | PydanticObjectId,
        **updates
    ) -> Optional[UserSettings]:
        """Update user settings fields."""
        settings = await self.get_user_settings(user_id)
        if not settings:
            return None
        
        updates['updated_at'] = datetime.utcnow()
        await settings.update({"$set": updates})
        return await self.get_user_settings(user_id)
    
    # ==========================================
    # USER SESSION OPERATIONS
    # ==========================================
    
    async def create_session(
        self,
        user_id: str | PydanticObjectId,
        refresh_token: str,
        expires_days: int = 7,
        **kwargs
    ) -> UserSession:
        """Create a new user session."""
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        session = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=expires_days),
            **kwargs
        )
        await session.insert()
        return session
    
    async def get_session_by_token(self, refresh_token: str) -> Optional[UserSession]:
        """Get session by refresh token."""
        return await UserSession.find_one(
            UserSession.refresh_token == refresh_token,
            UserSession.is_active == True
        )
    
    async def invalidate_session(self, refresh_token: str) -> bool:
        """Invalidate a session by refresh token."""
        session = await self.get_session_by_token(refresh_token)
        if not session:
            return False
        
        await session.update({"$set": {"is_active": False}})
        return True
    
    async def invalidate_all_user_sessions(self, user_id: str | PydanticObjectId) -> int:
        """Invalidate all sessions for a user."""
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        result = await UserSession.find(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).update({"$set": {"is_active": False}})
        
        return result.modified_count if result else 0
    
    async def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions."""
        result = await UserSession.find(
            UserSession.expires_at < datetime.utcnow()
        ).delete()
        return result.deleted_count if result else 0
    
    # ==========================================
    # ONBOARDING OPERATIONS
    # ==========================================
    
    async def create_onboarding_progress(self, user_id: PydanticObjectId) -> OnboardingProgress:
        """Create initial onboarding progress."""
        progress = OnboardingProgress(user_id=user_id)
        await progress.insert()
        return progress
    
    async def get_onboarding_progress(self, user_id: str | PydanticObjectId) -> Optional[OnboardingProgress]:
        """Get onboarding progress by user ID."""
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        return await OnboardingProgress.find_one(OnboardingProgress.user_id == user_id)
    
    async def update_onboarding_progress(
        self,
        user_id: str | PydanticObjectId,
        **updates
    ) -> Optional[OnboardingProgress]:
        """Update onboarding progress."""
        progress = await self.get_onboarding_progress(user_id)
        if not progress:
            return None
        
        updates['updated_at'] = datetime.utcnow()
        await progress.update({"$set": updates})
        return await self.get_onboarding_progress(user_id)


# Singleton repository instance
user_repository = UserRepository()


def get_user_repository() -> UserRepository:
    """Get the user repository instance."""
    return user_repository
