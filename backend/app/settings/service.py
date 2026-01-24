"""
Settings Service - Handles user settings management with MongoDB backend
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .schemas import (
    AccountSettings,
    NotificationSettings,
    NotificationSettingsUpdate,
    PrivacySettings,
    PrivacySettingsUpdate,
    AppearanceSettings,
    AppearanceSettingsUpdate,
    CalendarSettings,
    CalendarSettingsUpdate,
    AISettings,
    AISettingsUpdate,
    AllSettings,
    HelpCategory,
    HelpArticle,
    ThemeMode,
    LanguageCode
)
from app.database import (
    user_repository,
    get_user_repository,
    UserSettings as DbUserSettings,
    NotificationSettings as DbNotificationSettings,
    PrivacySettings as DbPrivacySettings,
    AppearanceSettings as DbAppearanceSettings,
)

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing user settings with MongoDB"""
    
    # Default help categories
    HELP_CATEGORIES = [
        HelpCategory(
            id="getting-started",
            title="Getting Started",
            icon="play-circle",
            description="Learn the basics of StyleX"
        ),
        HelpCategory(
            id="style-profile",
            title="Style Profile",
            icon="user",
            description="Setting up your style preferences"
        ),
        HelpCategory(
            id="ai-stylist",
            title="AI Stylist",
            icon="sparkles",
            description="Using the AI styling features"
        ),
        HelpCategory(
            id="calendar",
            title="Calendar Integration",
            icon="calendar",
            description="Syncing and managing your calendar"
        ),
        HelpCategory(
            id="account",
            title="Account & Billing",
            icon="credit-card",
            description="Manage your account and subscription"
        ),
        HelpCategory(
            id="troubleshooting",
            title="Troubleshooting",
            icon="tool",
            description="Common issues and solutions"
        )
    ]
    
    def __init__(self):
        """Initialize settings service"""
        self._repo = get_user_repository()
    
    async def _get_db_settings(self, user_id: str) -> Optional[DbUserSettings]:
        """Get settings from database"""
        return await self._repo.get_user_settings(user_id)
    
    # ============== Account Settings ==============
    
    async def get_account_settings(self, user_id: str, email: str = "user@example.com") -> AccountSettings:
        """Get account settings"""
        user = await self._repo.get_user_by_id(user_id)
        db_settings = await self._get_db_settings(user_id)
        
        return AccountSettings(
            user_id=user_id,
            email=user.email if user else email,
            email_verified=user.email_verified if user else False,
            two_factor_enabled=db_settings.two_factor_enabled if db_settings else False
        )
    
    async def update_email(self, user_id: str, new_email: str) -> bool:
        """Update user email"""
        result = await self._repo.update_user(user_id, email=new_email, email_verified=False)
        return result is not None
    
    async def enable_two_factor(self, user_id: str) -> Dict[str, Any]:
        """Enable two-factor authentication"""
        result = await self._repo.update_user_settings(user_id, two_factor_enabled=True)
        if result:
            return {
                "success": True,
                "message": "Two-factor authentication enabled",
                "secret": "DEMO_SECRET_KEY"  # Would be real TOTP secret
            }
        return {"success": False, "message": "Settings not found"}
    
    # ============== Notification Settings ==============
    
    async def get_notification_settings(self, user_id: str) -> NotificationSettings:
        """Get notification settings"""
        db_settings = await self._get_db_settings(user_id)
        
        if db_settings and db_settings.notifications:
            return NotificationSettings(
                user_id=user_id,
                email_notifications=db_settings.notifications.email_enabled,
                push_notifications=db_settings.notifications.push_enabled,
                outfit_suggestions=db_settings.notifications.outfit_suggestions,
                weather_alerts=db_settings.notifications.weather_alerts,
                event_reminders=db_settings.notifications.event_reminders,
                weekly_digest=db_settings.notifications.weekly_digest,
                marketing_emails=db_settings.notifications.marketing
            )
        
        return NotificationSettings(user_id=user_id)
    
    async def update_notification_settings(
        self,
        user_id: str,
        update_data: NotificationSettingsUpdate
    ) -> NotificationSettings:
        """Update notification settings"""
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        # Map to database model field names
        db_updates = {}
        if 'email_notifications' in update_dict:
            db_updates['notifications.email_enabled'] = update_dict['email_notifications']
        if 'push_notifications' in update_dict:
            db_updates['notifications.push_enabled'] = update_dict['push_notifications']
        if 'outfit_suggestions' in update_dict:
            db_updates['notifications.outfit_suggestions'] = update_dict['outfit_suggestions']
        if 'weather_alerts' in update_dict:
            db_updates['notifications.weather_alerts'] = update_dict['weather_alerts']
        if 'event_reminders' in update_dict:
            db_updates['notifications.event_reminders'] = update_dict['event_reminders']
        if 'weekly_digest' in update_dict:
            db_updates['notifications.weekly_digest'] = update_dict['weekly_digest']
        if 'marketing_emails' in update_dict:
            db_updates['notifications.marketing'] = update_dict['marketing_emails']
        
        if db_updates:
            await self._repo.update_user_settings(user_id, **db_updates)
        
        return await self.get_notification_settings(user_id)
    
    # ============== Privacy Settings ==============
    
    async def get_privacy_settings(self, user_id: str) -> PrivacySettings:
        """Get privacy settings"""
        db_settings = await self._get_db_settings(user_id)
        
        if db_settings and db_settings.privacy:
            return PrivacySettings(
                user_id=user_id,
                profile_visibility=db_settings.privacy.profile_visibility,
                show_wardrobe=db_settings.privacy.show_wardrobe,
                show_style_profile=db_settings.privacy.show_style_profile,
                allow_analytics=db_settings.privacy.analytics_enabled,
                allow_personalization=db_settings.privacy.personalization_enabled
            )
        
        return PrivacySettings(user_id=user_id)
    
    async def update_privacy_settings(
        self,
        user_id: str,
        update_data: PrivacySettingsUpdate
    ) -> PrivacySettings:
        """Update privacy settings"""
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        # Map to database model field names
        db_updates = {}
        if 'profile_visibility' in update_dict:
            db_updates['privacy.profile_visibility'] = update_dict['profile_visibility']
        if 'show_wardrobe' in update_dict:
            db_updates['privacy.show_wardrobe'] = update_dict['show_wardrobe']
        if 'show_style_profile' in update_dict:
            db_updates['privacy.show_style_profile'] = update_dict['show_style_profile']
        if 'allow_analytics' in update_dict:
            db_updates['privacy.analytics_enabled'] = update_dict['allow_analytics']
        if 'allow_personalization' in update_dict:
            db_updates['privacy.personalization_enabled'] = update_dict['allow_personalization']
        
        if db_updates:
            await self._repo.update_user_settings(user_id, **db_updates)
        
        return await self.get_privacy_settings(user_id)
    
    # ============== Appearance Settings ==============
    
    async def get_appearance_settings(self, user_id: str) -> AppearanceSettings:
        """Get appearance settings"""
        db_settings = await self._get_db_settings(user_id)
        
        if db_settings and db_settings.appearance:
            return AppearanceSettings(
                user_id=user_id,
                theme=ThemeMode(db_settings.appearance.theme) if db_settings.appearance.theme else ThemeMode.SYSTEM,
                language=LanguageCode(db_settings.appearance.language) if db_settings.appearance.language else LanguageCode.EN,
                compact_view=db_settings.appearance.compact_view,
                show_outfit_scores=db_settings.appearance.show_outfit_scores
            )
        
        return AppearanceSettings(user_id=user_id)
    
    async def update_appearance_settings(
        self,
        user_id: str,
        update_data: AppearanceSettingsUpdate
    ) -> AppearanceSettings:
        """Update appearance settings"""
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        db_updates = {}
        if 'theme' in update_dict:
            db_updates['appearance.theme'] = update_dict['theme']
        if 'language' in update_dict:
            db_updates['appearance.language'] = update_dict['language']
        if 'compact_view' in update_dict:
            db_updates['appearance.compact_view'] = update_dict['compact_view']
        if 'show_outfit_scores' in update_dict:
            db_updates['appearance.show_outfit_scores'] = update_dict['show_outfit_scores']
        
        if db_updates:
            await self._repo.update_user_settings(user_id, **db_updates)
        
        return await self.get_appearance_settings(user_id)
    
    # ============== Calendar Settings ==============
    
    async def get_calendar_settings(self, user_id: str) -> CalendarSettings:
        """Get calendar settings"""
        db_settings = await self._get_db_settings(user_id)
        
        if db_settings:
            return CalendarSettings(
                user_id=user_id,
                google_connected=db_settings.google_calendar_connected,
                google_email=db_settings.google_calendar_email,
                calendars_synced=db_settings.synced_calendars or [],
                default_outfit_lead_time=db_settings.outfit_lead_time_hours or 24,
                auto_suggest_outfits=db_settings.auto_suggest_outfits
            )
        
        return CalendarSettings(user_id=user_id)
    
    async def update_calendar_settings(
        self,
        user_id: str,
        update_data: CalendarSettingsUpdate
    ) -> CalendarSettings:
        """Update calendar settings"""
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        db_updates = {}
        if 'calendars_synced' in update_dict:
            db_updates['synced_calendars'] = update_dict['calendars_synced']
        if 'default_outfit_lead_time' in update_dict:
            db_updates['outfit_lead_time_hours'] = update_dict['default_outfit_lead_time']
        if 'auto_suggest_outfits' in update_dict:
            db_updates['auto_suggest_outfits'] = update_dict['auto_suggest_outfits']
        
        if db_updates:
            await self._repo.update_user_settings(user_id, **db_updates)
        
        return await self.get_calendar_settings(user_id)
    
    async def connect_google_calendar(self, user_id: str, email: str) -> CalendarSettings:
        """Mark Google Calendar as connected"""
        await self._repo.update_user_settings(
            user_id,
            google_calendar_connected=True,
            google_calendar_email=email
        )
        return await self.get_calendar_settings(user_id)
    
    async def disconnect_google_calendar(self, user_id: str) -> CalendarSettings:
        """Disconnect Google Calendar"""
        await self._repo.update_user_settings(
            user_id,
            google_calendar_connected=False,
            google_calendar_email=None,
            synced_calendars=[]
        )
        return await self.get_calendar_settings(user_id)
    
    # ============== AI Settings ==============
    
    async def get_ai_settings(self, user_id: str) -> AISettings:
        """Get AI settings"""
        db_settings = await self._get_db_settings(user_id)
        
        if db_settings:
            return AISettings(
                user_id=user_id,
                personality=db_settings.ai_personality or "friendly",
                verbosity=db_settings.ai_verbosity or "balanced",
                auto_suggestions=db_settings.auto_suggest_outfits,
                learn_from_feedback=True  # Default value
            )
        
        return AISettings(user_id=user_id)
    
    async def update_ai_settings(
        self,
        user_id: str,
        update_data: AISettingsUpdate
    ) -> AISettings:
        """Update AI settings"""
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        
        db_updates = {}
        if 'personality' in update_dict:
            db_updates['ai_personality'] = update_dict['personality']
        if 'verbosity' in update_dict:
            db_updates['ai_verbosity'] = update_dict['verbosity']
        if 'auto_suggestions' in update_dict:
            db_updates['auto_suggest_outfits'] = update_dict['auto_suggestions']
        
        if db_updates:
            await self._repo.update_user_settings(user_id, **db_updates)
        
        return await self.get_ai_settings(user_id)
    
    # ============== All Settings ==============
    
    async def get_all_settings(self, user_id: str, email: str = "user@example.com") -> AllSettings:
        """Get all settings for a user"""
        return AllSettings(
            user_id=user_id,
            account=await self.get_account_settings(user_id, email),
            notifications=await self.get_notification_settings(user_id),
            privacy=await self.get_privacy_settings(user_id),
            appearance=await self.get_appearance_settings(user_id),
            calendar=await self.get_calendar_settings(user_id),
            ai=await self.get_ai_settings(user_id)
        )
    
    async def reset_settings(self, user_id: str, category: Optional[str] = None) -> bool:
        """Reset settings to defaults"""
        from beanie import PydanticObjectId
        
        if category:
            # Reset specific category
            reset_updates = {}
            if category == 'notifications':
                reset_updates['notifications'] = DbNotificationSettings()
            elif category == 'privacy':
                reset_updates['privacy'] = DbPrivacySettings()
            elif category == 'appearance':
                reset_updates['appearance'] = DbAppearanceSettings()
            
            if reset_updates:
                await self._repo.update_user_settings(user_id, **reset_updates)
        else:
            # Reset all settings - delete and recreate
            user_id_obj = PydanticObjectId(user_id) if isinstance(user_id, str) else user_id
            await DbUserSettings.find(DbUserSettings.user_id == user_id_obj).delete()
            await self._repo.create_user_settings(user_id_obj)
        
        return True
    
    # ============== Help & Support ==============
    
    def get_help_categories(self) -> List[HelpCategory]:
        """Get help categories"""
        return self.HELP_CATEGORIES
    
    def get_help_articles(self, category_id: str) -> List[HelpArticle]:
        """Get help articles for a category"""
        # Mock articles - would come from CMS in production
        articles_map = {
            "getting-started": [
                HelpArticle(
                    id="gs-1",
                    category_id="getting-started",
                    title="Welcome to StyleX",
                    content="Learn how to get started with StyleX...",
                    tags=["intro", "basics"]
                ),
                HelpArticle(
                    id="gs-2",
                    category_id="getting-started",
                    title="Complete Your Profile",
                    content="Setting up your style profile helps us...",
                    tags=["profile", "onboarding"]
                )
            ],
            "ai-stylist": [
                HelpArticle(
                    id="ai-1",
                    category_id="ai-stylist",
                    title="How AI Styling Works",
                    content="Our AI stylist uses advanced algorithms...",
                    tags=["ai", "recommendations"]
                )
            ]
        }
        
        return articles_map.get(category_id, [])
    
    async def submit_feedback(
        self,
        user_id: str,
        rating: int,
        feedback: Optional[str] = None,
        feature: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit user feedback"""
        # Store feedback in database
        from app.database import ChatMessage
        from beanie import PydanticObjectId
        
        user_id_obj = PydanticObjectId(user_id) if isinstance(user_id, str) else user_id
        
        # Store as a system message/feedback entry
        feedback_msg = ChatMessage(
            user_id=user_id_obj,
            role="system",
            content=f"Feedback (rating: {rating}): {feedback or 'No comment'}",
            metadata={
                "type": "feedback",
                "rating": rating,
                "feature": feature
            }
        )
        await feedback_msg.insert()
        
        return {
            "success": True,
            "message": "Thank you for your feedback!",
            "feedback_id": str(feedback_msg.id)
        }
    
    async def submit_support_request(
        self,
        user_id: str,
        subject: str,
        message: str,
        category: str = "general"
    ) -> Dict[str, Any]:
        """Submit support request"""
        from app.database import ChatMessage
        from beanie import PydanticObjectId
        
        user_id_obj = PydanticObjectId(user_id) if isinstance(user_id, str) else user_id
        
        ticket_id = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{str(user_id_obj)[-4:]}"
        
        # Store support request
        support_msg = ChatMessage(
            user_id=user_id_obj,
            role="system",
            content=f"Support Request ({category}): {subject}\n\n{message}",
            metadata={
                "type": "support_request",
                "ticket_id": ticket_id,
                "category": category,
                "subject": subject
            }
        )
        await support_msg.insert()
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": f"Support ticket {ticket_id} created. We'll respond within 24 hours."
        }
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data (GDPR compliance)"""
        from beanie import PydanticObjectId
        from app.database import (
            User, UserProfile as DbProfile, ClothingItem,
            OutfitRecommendation, CalendarEvent, ChatMessage
        )
        
        user_id_obj = PydanticObjectId(user_id) if isinstance(user_id, str) else user_id
        
        # Gather all user data
        user = await self._repo.get_user_by_id(user_id)
        profile = await self._repo.get_user_profile(user_id)
        settings = await self._repo.get_user_settings(user_id)
        
        # Get related collections
        clothing = await ClothingItem.find(ClothingItem.user_id == user_id_obj).to_list()
        recommendations = await OutfitRecommendation.find(OutfitRecommendation.user_id == user_id_obj).to_list()
        events = await CalendarEvent.find(CalendarEvent.user_id == user_id_obj).to_list()
        messages = await ChatMessage.find(ChatMessage.user_id == user_id_obj).to_list()
        
        return {
            "user_id": user_id,
            "exported_at": datetime.utcnow().isoformat(),
            "user": user.model_dump() if user else None,
            "profile": profile.model_dump() if profile else None,
            "settings": settings.model_dump() if settings else None,
            "clothing_items": [c.model_dump() for c in clothing],
            "recommendations": [r.model_dump() for r in recommendations],
            "calendar_events": [e.model_dump() for e in events],
            "chat_messages": [m.model_dump() for m in messages]
        }
    
    async def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data (GDPR compliance)"""
        return await self._repo.delete_user(user_id)


# Singleton instance
_service_instance: Optional[SettingsService] = None


def get_settings_service() -> SettingsService:
    """Get or create the Settings service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = SettingsService()
    return _service_instance
