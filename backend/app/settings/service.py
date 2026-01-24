"""
Settings Service - Handles user settings management
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

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing user settings"""
    
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
        # In-memory storage (use DB in production)
        self._settings: Dict[str, Dict[str, Any]] = {}
    
    def _get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """Get or create settings dict for user"""
        if user_id not in self._settings:
            self._settings[user_id] = {
                "account": None,
                "notifications": None,
                "privacy": None,
                "appearance": None,
                "calendar": None,
                "ai": None
            }
        return self._settings[user_id]
    
    # ============== Account Settings ==============
    
    async def get_account_settings(self, user_id: str, email: str = "user@example.com") -> AccountSettings:
        """Get account settings"""
        settings = self._get_user_settings(user_id)
        
        if not settings["account"]:
            settings["account"] = AccountSettings(
                user_id=user_id,
                email=email
            )
        
        return settings["account"]
    
    async def update_email(self, user_id: str, new_email: str) -> bool:
        """Update user email"""
        settings = self._get_user_settings(user_id)
        if settings["account"]:
            settings["account"].email = new_email
            settings["account"].email_verified = False
            return True
        return False
    
    async def enable_two_factor(self, user_id: str) -> Dict[str, str]:
        """Enable two-factor authentication"""
        settings = self._get_user_settings(user_id)
        if settings["account"]:
            settings["account"].two_factor_enabled = True
            return {
                "success": True,
                "message": "Two-factor authentication enabled",
                "secret": "DEMO_SECRET_KEY"  # Would be real TOTP secret
            }
        return {"success": False, "message": "Account not found"}
    
    # ============== Notification Settings ==============
    
    async def get_notification_settings(self, user_id: str) -> NotificationSettings:
        """Get notification settings"""
        settings = self._get_user_settings(user_id)
        
        if not settings["notifications"]:
            settings["notifications"] = NotificationSettings(user_id=user_id)
        
        return settings["notifications"]
    
    async def update_notification_settings(
        self,
        user_id: str,
        update_data: NotificationSettingsUpdate
    ) -> NotificationSettings:
        """Update notification settings"""
        current = await self.get_notification_settings(user_id)
        
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in update_dict.items():
            if hasattr(current, field):
                setattr(current, field, value)
        
        self._settings[user_id]["notifications"] = current
        return current
    
    # ============== Privacy Settings ==============
    
    async def get_privacy_settings(self, user_id: str) -> PrivacySettings:
        """Get privacy settings"""
        settings = self._get_user_settings(user_id)
        
        if not settings["privacy"]:
            settings["privacy"] = PrivacySettings(user_id=user_id)
        
        return settings["privacy"]
    
    async def update_privacy_settings(
        self,
        user_id: str,
        update_data: PrivacySettingsUpdate
    ) -> PrivacySettings:
        """Update privacy settings"""
        current = await self.get_privacy_settings(user_id)
        
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in update_dict.items():
            if hasattr(current, field):
                setattr(current, field, value)
        
        self._settings[user_id]["privacy"] = current
        return current
    
    # ============== Appearance Settings ==============
    
    async def get_appearance_settings(self, user_id: str) -> AppearanceSettings:
        """Get appearance settings"""
        settings = self._get_user_settings(user_id)
        
        if not settings["appearance"]:
            settings["appearance"] = AppearanceSettings(user_id=user_id)
        
        return settings["appearance"]
    
    async def update_appearance_settings(
        self,
        user_id: str,
        update_data: AppearanceSettingsUpdate
    ) -> AppearanceSettings:
        """Update appearance settings"""
        current = await self.get_appearance_settings(user_id)
        
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in update_dict.items():
            if hasattr(current, field):
                setattr(current, field, value)
        
        self._settings[user_id]["appearance"] = current
        return current
    
    # ============== Calendar Settings ==============
    
    async def get_calendar_settings(self, user_id: str) -> CalendarSettings:
        """Get calendar settings"""
        settings = self._get_user_settings(user_id)
        
        if not settings["calendar"]:
            settings["calendar"] = CalendarSettings(user_id=user_id)
        
        return settings["calendar"]
    
    async def update_calendar_settings(
        self,
        user_id: str,
        update_data: CalendarSettingsUpdate
    ) -> CalendarSettings:
        """Update calendar settings"""
        current = await self.get_calendar_settings(user_id)
        
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in update_dict.items():
            if hasattr(current, field):
                setattr(current, field, value)
        
        self._settings[user_id]["calendar"] = current
        return current
    
    async def connect_google_calendar(self, user_id: str, email: str) -> CalendarSettings:
        """Mark Google Calendar as connected"""
        settings = await self.get_calendar_settings(user_id)
        settings.google_connected = True
        settings.google_email = email
        self._settings[user_id]["calendar"] = settings
        return settings
    
    async def disconnect_google_calendar(self, user_id: str) -> CalendarSettings:
        """Disconnect Google Calendar"""
        settings = await self.get_calendar_settings(user_id)
        settings.google_connected = False
        settings.google_email = None
        settings.calendars_synced = []
        self._settings[user_id]["calendar"] = settings
        return settings
    
    # ============== AI Settings ==============
    
    async def get_ai_settings(self, user_id: str) -> AISettings:
        """Get AI settings"""
        settings = self._get_user_settings(user_id)
        
        if not settings["ai"]:
            settings["ai"] = AISettings(user_id=user_id)
        
        return settings["ai"]
    
    async def update_ai_settings(
        self,
        user_id: str,
        update_data: AISettingsUpdate
    ) -> AISettings:
        """Update AI settings"""
        current = await self.get_ai_settings(user_id)
        
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        for field, value in update_dict.items():
            if hasattr(current, field):
                setattr(current, field, value)
        
        self._settings[user_id]["ai"] = current
        return current
    
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
        if user_id in self._settings:
            if category and category in self._settings[user_id]:
                self._settings[user_id][category] = None
            else:
                del self._settings[user_id]
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
        # Would save to database in production
        return {
            "success": True,
            "message": "Thank you for your feedback!",
            "feedback_id": f"fb_{user_id}_{datetime.utcnow().timestamp()}"
        }
    
    async def submit_support_request(
        self,
        user_id: str,
        subject: str,
        message: str,
        category: str = "general"
    ) -> Dict[str, Any]:
        """Submit support request"""
        # Would create support ticket in production
        ticket_id = f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-001"
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": f"Support ticket {ticket_id} created. We'll respond within 24 hours."
        }
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data (GDPR compliance)"""
        settings = self._get_user_settings(user_id)
        
        return {
            "user_id": user_id,
            "exported_at": datetime.utcnow().isoformat(),
            "settings": {
                k: v.model_dump() if v else None 
                for k, v in settings.items()
            }
        }
    
    async def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data (GDPR compliance)"""
        if user_id in self._settings:
            del self._settings[user_id]
        return True


# Singleton instance
_service_instance: Optional[SettingsService] = None


def get_settings_service() -> SettingsService:
    """Get or create the Settings service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = SettingsService()
    return _service_instance
