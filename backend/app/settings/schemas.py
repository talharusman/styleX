"""
Pydantic schemas for Settings endpoints
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class ThemeMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class LanguageCode(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    ZH = "zh"
    JA = "ja"
    KO = "ko"
    AR = "ar"


class NotificationChannel(str, Enum):
    PUSH = "push"
    EMAIL = "email"
    SMS = "sms"


class AccountSettings(BaseModel):
    """User account settings"""
    user_id: str
    email: EmailStr
    email_verified: bool = False
    phone: Optional[str] = None
    phone_verified: bool = False
    two_factor_enabled: bool = False
    login_alerts: bool = True
    last_password_change: Optional[datetime] = None


class NotificationSettings(BaseModel):
    """Notification preferences"""
    user_id: str
    
    # Push notifications
    push_enabled: bool = True
    push_outfit_reminders: bool = True
    push_weather_alerts: bool = True
    push_event_reminders: bool = True
    push_ai_suggestions: bool = True
    push_promotions: bool = False
    
    # Email notifications
    email_enabled: bool = True
    email_daily_digest: bool = False
    email_weekly_summary: bool = True
    email_outfit_recommendations: bool = True
    email_promotions: bool = False
    
    # SMS notifications
    sms_enabled: bool = False
    sms_urgent_only: bool = True
    
    # Timing preferences
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = "22:00"
    quiet_hours_end: Optional[str] = "08:00"


class NotificationSettingsUpdate(BaseModel):
    """Update notification settings"""
    push_enabled: Optional[bool] = None
    push_outfit_reminders: Optional[bool] = None
    push_weather_alerts: Optional[bool] = None
    push_event_reminders: Optional[bool] = None
    push_ai_suggestions: Optional[bool] = None
    push_promotions: Optional[bool] = None
    
    email_enabled: Optional[bool] = None
    email_daily_digest: Optional[bool] = None
    email_weekly_summary: Optional[bool] = None
    email_outfit_recommendations: Optional[bool] = None
    email_promotions: Optional[bool] = None
    
    sms_enabled: Optional[bool] = None
    sms_urgent_only: Optional[bool] = None
    
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class PrivacySettings(BaseModel):
    """Privacy settings"""
    user_id: str
    
    # Profile visibility
    profile_public: bool = False
    show_favorites: bool = False
    show_outfits: bool = False
    
    # Data collection
    analytics_enabled: bool = True
    personalization_enabled: bool = True
    ai_training_consent: bool = False
    
    # Third-party sharing
    share_with_partners: bool = False
    targeted_ads: bool = False
    
    # Activity
    save_search_history: bool = True
    save_chat_history: bool = True


class PrivacySettingsUpdate(BaseModel):
    """Update privacy settings"""
    profile_public: Optional[bool] = None
    show_favorites: Optional[bool] = None
    show_outfits: Optional[bool] = None
    
    analytics_enabled: Optional[bool] = None
    personalization_enabled: Optional[bool] = None
    ai_training_consent: Optional[bool] = None
    
    share_with_partners: Optional[bool] = None
    targeted_ads: Optional[bool] = None
    
    save_search_history: Optional[bool] = None
    save_chat_history: Optional[bool] = None


class AppearanceSettings(BaseModel):
    """Appearance/UI settings"""
    user_id: str
    theme: ThemeMode = ThemeMode.SYSTEM
    language: LanguageCode = LanguageCode.EN
    font_size: str = "medium"  # small, medium, large
    high_contrast: bool = False
    reduce_motion: bool = False
    compact_mode: bool = False


class AppearanceSettingsUpdate(BaseModel):
    """Update appearance settings"""
    theme: Optional[ThemeMode] = None
    language: Optional[LanguageCode] = None
    font_size: Optional[str] = None
    high_contrast: Optional[bool] = None
    reduce_motion: Optional[bool] = None
    compact_mode: Optional[bool] = None


class CalendarSettings(BaseModel):
    """Calendar integration settings"""
    user_id: str
    google_connected: bool = False
    google_email: Optional[str] = None
    sync_enabled: bool = True
    auto_outfit_suggestions: bool = True
    default_reminder_minutes: int = 30
    sync_interval_minutes: int = 15
    calendars_synced: List[str] = Field(default_factory=list)


class CalendarSettingsUpdate(BaseModel):
    """Update calendar settings"""
    sync_enabled: Optional[bool] = None
    auto_outfit_suggestions: Optional[bool] = None
    default_reminder_minutes: Optional[int] = None
    sync_interval_minutes: Optional[int] = None
    calendars_synced: Optional[List[str]] = None


class AISettings(BaseModel):
    """AI assistant settings"""
    user_id: str
    ai_enabled: bool = True
    style_suggestions: bool = True
    weather_based_recommendations: bool = True
    event_based_recommendations: bool = True
    learning_enabled: bool = True
    response_style: str = "friendly"  # friendly, professional, casual
    include_budget_in_recommendations: bool = False


class AISettingsUpdate(BaseModel):
    """Update AI settings"""
    ai_enabled: Optional[bool] = None
    style_suggestions: Optional[bool] = None
    weather_based_recommendations: Optional[bool] = None
    event_based_recommendations: Optional[bool] = None
    learning_enabled: Optional[bool] = None
    response_style: Optional[str] = None
    include_budget_in_recommendations: Optional[bool] = None


class AllSettings(BaseModel):
    """Complete settings bundle"""
    user_id: str
    account: AccountSettings
    notifications: NotificationSettings
    privacy: PrivacySettings
    appearance: AppearanceSettings
    calendar: CalendarSettings
    ai: AISettings
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HelpCategory(BaseModel):
    """Help/FAQ category"""
    id: str
    title: str
    icon: str
    description: str


class HelpArticle(BaseModel):
    """Help article"""
    id: str
    category_id: str
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)


class ContactSupportRequest(BaseModel):
    """Contact support request"""
    subject: str = Field(..., max_length=200)
    message: str = Field(..., max_length=5000)
    category: str = "general"
    attachments: List[str] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    """User feedback request"""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = Field(default=None, max_length=2000)
    feature: Optional[str] = None
    would_recommend: Optional[bool] = None
