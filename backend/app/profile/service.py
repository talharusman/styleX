"""
Profile Service - Handles user profile management
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .schemas import (
    UserProfile,
    ProfileUpdate,
    StyleProfile,
    ProfileStats,
    ProfileSummary,
    SubscriptionTier,
    ProfileVisibility
)

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles"""
    
    def __init__(self):
        """Initialize profile service"""
        # In-memory storage (use DB in production)
        self._profiles: Dict[str, UserProfile] = {}
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        return self._profiles.get(user_id)
    
    async def create_profile(
        self,
        user_id: str,
        email: str,
        name: str,
        **kwargs
    ) -> UserProfile:
        """Create a new user profile"""
        profile = UserProfile(
            id=user_id,
            email=email,
            name=name,
            **kwargs
        )
        
        self._profiles[user_id] = profile
        return profile
    
    async def update_profile(
        self,
        user_id: str,
        update_data: ProfileUpdate
    ) -> Optional[UserProfile]:
        """Update user profile"""
        profile = await self.get_profile(user_id)
        
        if not profile:
            return None
        
        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        for field, value in update_dict.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        self._profiles[user_id] = profile
        
        return profile
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile"""
        if user_id in self._profiles:
            del self._profiles[user_id]
            return True
        return False
    
    async def get_style_profile(self, user_id: str) -> Optional[StyleProfile]:
        """Get user's style profile"""
        profile = await self.get_profile(user_id)
        
        if not profile:
            return None
        
        return StyleProfile(
            user_id=user_id,
            body_type=profile.body_type,
            skin_tone=profile.skin_tone,
            undertone=profile.undertone,
            seasonal_type=profile.seasonal_type,
            primary_style=profile.primary_style,
            secondary_styles=profile.secondary_styles,
            favorite_colors=profile.favorite_colors,
            avoid_colors=profile.avoid_colors,
            recommended_colors=profile.recommended_colors
        )
    
    async def update_style_profile(
        self,
        user_id: str,
        style_data: Dict[str, Any]
    ) -> Optional[StyleProfile]:
        """Update user's style profile"""
        profile = await self.get_profile(user_id)
        
        if not profile:
            return None
        
        # Update style-related fields
        style_fields = [
            'body_type', 'skin_tone', 'undertone', 'seasonal_type',
            'primary_style', 'secondary_styles', 'favorite_colors',
            'avoid_colors', 'recommended_colors'
        ]
        
        for field in style_fields:
            if field in style_data:
                setattr(profile, field, style_data[field])
        
        profile.updated_at = datetime.utcnow()
        self._profiles[user_id] = profile
        
        return await self.get_style_profile(user_id)
    
    async def get_profile_stats(self, user_id: str) -> ProfileStats:
        """Get user's profile statistics"""
        profile = await self.get_profile(user_id)
        
        # Calculate days active
        days_active = 0
        if profile and profile.created_at:
            days_active = (datetime.utcnow() - profile.created_at).days
        
        # These would come from actual data in production
        return ProfileStats(
            user_id=user_id,
            outfits_created=15,
            outfits_favorited=8,
            wardrobe_items=42,
            events_synced=23,
            ai_chats=67,
            style_score=8.2,
            member_since=profile.created_at if profile else None,
            days_active=days_active
        )
    
    async def get_profile_summary(self, user_id: str) -> Optional[ProfileSummary]:
        """Get compact profile summary"""
        profile = await self.get_profile(user_id)
        
        if not profile:
            return None
        
        # Build style summary
        style_parts = []
        if profile.primary_style:
            style_parts.append(profile.primary_style)
        if profile.body_type:
            style_parts.append(f"{profile.body_type} body")
        if profile.seasonal_type:
            style_parts.append(f"{profile.seasonal_type} colors")
        
        style_summary = " | ".join(style_parts) if style_parts else "Style not set"
        
        return ProfileSummary(
            id=user_id,
            name=profile.name,
            avatar_url=profile.avatar_url,
            subscription_tier=profile.subscription_tier,
            style_summary=style_summary,
            location=profile.location
        )
    
    async def update_avatar(
        self,
        user_id: str,
        avatar_url: str
    ) -> bool:
        """Update user's avatar"""
        profile = await self.get_profile(user_id)
        
        if not profile:
            return False
        
        profile.avatar_url = avatar_url
        profile.updated_at = datetime.utcnow()
        self._profiles[user_id] = profile
        
        return True
    
    async def update_subscription(
        self,
        user_id: str,
        tier: SubscriptionTier,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Update user's subscription tier"""
        profile = await self.get_profile(user_id)
        
        if not profile:
            return False
        
        profile.subscription_tier = tier
        profile.subscription_expires = expires_at
        profile.updated_at = datetime.utcnow()
        self._profiles[user_id] = profile
        
        return True
    
    async def complete_onboarding(self, user_id: str) -> bool:
        """Mark user's onboarding as complete"""
        profile = await self.get_profile(user_id)
        
        if not profile:
            return False
        
        profile.onboarding_complete = True
        profile.updated_at = datetime.utcnow()
        self._profiles[user_id] = profile
        
        return True
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login time"""
        profile = await self.get_profile(user_id)
        
        if not profile:
            return False
        
        profile.last_login = datetime.utcnow()
        self._profiles[user_id] = profile
        
        return True
    
    def get_recommended_colors(
        self,
        skin_tone: str,
        undertone: str
    ) -> List[str]:
        """Get recommended colors based on skin tone and undertone"""
        # This could integrate with the onboarding service
        # For now, return default recommendations
        
        color_map = {
            ("fair", "cool"): ["navy", "burgundy", "forest green", "plum"],
            ("fair", "warm"): ["peach", "coral", "gold", "cream"],
            ("medium", "cool"): ["burgundy", "teal", "purple", "grey"],
            ("medium", "warm"): ["orange", "coral", "gold", "olive"],
            ("dark", "cool"): ["royal blue", "purple", "silver", "pink"],
            ("dark", "warm"): ["orange", "yellow", "gold", "emerald"]
        }
        
        key = (skin_tone.lower(), undertone.lower())
        return color_map.get(key, ["navy", "white", "grey"])


# Singleton instance
_service_instance: Optional[ProfileService] = None


def get_profile_service() -> ProfileService:
    """Get or create the Profile service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ProfileService()
    return _service_instance
