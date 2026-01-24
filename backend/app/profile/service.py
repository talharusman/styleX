"""
Profile Service - Handles user profile management with MongoDB backend
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
from app.database import (
    user_repository,
    get_user_repository,
    User,
    UserProfile as DbUserProfile,
    ClothingItem,
    OutfitRecommendation,
    ChatMessage,
)

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles with MongoDB"""
    
    def __init__(self):
        """Initialize profile service"""
        self._repo = get_user_repository()
    
    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        # Get user and profile from database
        user = await self._repo.get_user_by_id(user_id)
        if not user:
            return None
        
        db_profile = await self._repo.get_user_profile(user_id)
        
        # Build response profile from database models
        return UserProfile(
            id=str(user.id),
            email=user.email,
            name=user.name,
            avatar_url=db_profile.avatar_url if db_profile else None,
            body_type=db_profile.body_measurements.body_type if db_profile and db_profile.body_measurements else None,
            skin_tone=db_profile.skin_features.depth.value if db_profile and db_profile.skin_features else None,
            undertone=db_profile.skin_features.undertone.value if db_profile and db_profile.skin_features else None,
            seasonal_type=db_profile.skin_features.season.value if db_profile and db_profile.skin_features else None,
            primary_style=db_profile.style_preferences.primary_style.value if db_profile and db_profile.style_preferences and db_profile.style_preferences.primary_style else None,
            secondary_styles=[s.value for s in db_profile.style_preferences.secondary_styles] if db_profile and db_profile.style_preferences else [],
            favorite_colors=db_profile.style_preferences.favorite_colors if db_profile and db_profile.style_preferences else [],
            avoid_colors=db_profile.style_preferences.avoid_colors if db_profile and db_profile.style_preferences else [],
            recommended_colors=db_profile.style_preferences.recommended_colors if db_profile and db_profile.style_preferences else [],
            location=db_profile.location if db_profile else None,
            onboarding_complete=user.onboarding_completed,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    async def create_profile(
        self,
        user_id: str,
        email: str,
        name: str,
        **kwargs
    ) -> UserProfile:
        """Create a new user profile"""
        # Profile is created automatically when user is created
        # This is a fallback for any manual creation
        db_profile = await self._repo.get_user_profile(user_id)
        if not db_profile:
            from beanie import PydanticObjectId
            db_profile = await self._repo.create_user_profile(PydanticObjectId(user_id))
        
        return await self.get_profile(user_id)
    
    async def update_profile(
        self,
        user_id: str,
        update_data: ProfileUpdate
    ) -> Optional[UserProfile]:
        """Update user profile"""
        # Get existing profile
        db_profile = await self._repo.get_user_profile(user_id)
        if not db_profile:
            return None
        
        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        # Map update fields to database model structure
        profile_updates = {}
        
        # Direct fields
        if 'avatar_url' in update_dict:
            profile_updates['avatar_url'] = update_dict['avatar_url']
        if 'location' in update_dict:
            profile_updates['location'] = update_dict['location']
        
        if profile_updates:
            await self._repo.update_user_profile(user_id, **profile_updates)
        
        return await self.get_profile(user_id)
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile"""
        return await self._repo.delete_user(user_id)
    
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
        db_profile = await self._repo.get_user_profile(user_id)
        if not db_profile:
            return None
        
        # Update style preferences in database
        updates = {}
        
        # Map style fields to database structure
        style_pref_updates = {}
        if 'primary_style' in style_data:
            style_pref_updates['primary_style'] = style_data['primary_style']
        if 'secondary_styles' in style_data:
            style_pref_updates['secondary_styles'] = style_data['secondary_styles']
        if 'favorite_colors' in style_data:
            style_pref_updates['favorite_colors'] = style_data['favorite_colors']
        if 'avoid_colors' in style_data:
            style_pref_updates['avoid_colors'] = style_data['avoid_colors']
        if 'recommended_colors' in style_data:
            style_pref_updates['recommended_colors'] = style_data['recommended_colors']
        
        if style_pref_updates:
            updates['style_preferences'] = style_pref_updates
        
        # Skin features updates
        skin_updates = {}
        if 'skin_tone' in style_data:
            skin_updates['depth'] = style_data['skin_tone']
        if 'undertone' in style_data:
            skin_updates['undertone'] = style_data['undertone']
        if 'seasonal_type' in style_data:
            skin_updates['season'] = style_data['seasonal_type']
        
        if skin_updates:
            updates['skin_features'] = skin_updates
        
        if updates:
            await self._repo.update_user_profile(user_id, **updates)
        
        return await self.get_style_profile(user_id)
    
    async def get_profile_stats(self, user_id: str) -> ProfileStats:
        """Get user's profile statistics"""
        user = await self._repo.get_user_by_id(user_id)
        
        # Calculate days active
        days_active = 0
        if user and user.created_at:
            days_active = (datetime.utcnow() - user.created_at).days
        
        # Get actual counts from database
        from beanie import PydanticObjectId
        user_oid = PydanticObjectId(user_id) if isinstance(user_id, str) else user_id
        
        wardrobe_count = await ClothingItem.find(ClothingItem.user_id == user_oid).count()
        chat_count = await ChatMessage.find(ChatMessage.user_id == user_oid).count()
        
        return ProfileStats(
            user_id=user_id,
            outfits_created=0,  # TODO: Count from OutfitRecommendation
            outfits_favorited=0,  # TODO: Track favorites
            wardrobe_items=wardrobe_count,
            events_synced=0,  # TODO: Count from CalendarEvent
            ai_chats=chat_count,
            style_score=0.0,  # TODO: Calculate style score
            member_since=user.created_at if user else None,
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
            subscription_tier=profile.subscription_tier if hasattr(profile, 'subscription_tier') else SubscriptionTier.FREE,
            style_summary=style_summary,
            location=profile.location
        )
    
    async def update_avatar(
        self,
        user_id: str,
        avatar_url: str
    ) -> bool:
        """Update user's avatar"""
        result = await self._repo.update_user_profile(user_id, avatar_url=avatar_url)
        return result is not None
    
    async def update_subscription(
        self,
        user_id: str,
        tier: SubscriptionTier,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Update user's subscription tier"""
        result = await self._repo.update_user(
            user_id,
            subscription_tier=tier.value,
            subscription_expires=expires_at
        )
        return result is not None
    
    async def complete_onboarding(self, user_id: str) -> bool:
        """Mark user's onboarding as complete"""
        result = await self._repo.update_user(user_id, onboarding_completed=True)
        return result is not None
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login time"""
        await self._repo.update_last_login(user_id)
        return True
    
    def get_recommended_colors(
        self,
        skin_tone: str,
        undertone: str
    ) -> List[str]:
        """Get recommended colors based on skin tone and undertone"""
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
