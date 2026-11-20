"""
MongoDB Document Models using Beanie ODM.

Defines all data structures for StyleX application.
Each Document class maps to a MongoDB collection.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from beanie import Document, Indexed, Link, PydanticObjectId
from pydantic import BaseModel, Field, EmailStr


# ============================================
# ENUMS
# ============================================

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class Undertone(str, Enum):
    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"


class SkinDepth(str, Enum):
    FAIR = "fair"
    LIGHT = "light"
    MEDIUM = "medium"
    TAN = "tan"
    DEEP = "deep"


class Season(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


class ClothingCategory(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    DRESS = "dress"
    OUTERWEAR = "outerwear"
    ACCESSORY = "accessory"
    FOOTWEAR = "footwear"
    UNKNOWN = "unknown"


class StyleType(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    BUSINESS = "business"
    SPORTY = "sporty"
    BOHEMIAN = "bohemian"
    VINTAGE = "vintage"
    STREETWEAR = "streetwear"
    MINIMALIST = "minimalist"
    PARTY = "party"


class WeatherType(str, Enum):
    SUMMER = "summer"
    WINTER = "winter"
    SPRING = "spring"
    FALL = "fall"
    ALL_SEASON = "all_season"


class DesignPattern(str, Enum):
    PLAIN = "plain"
    STRIPES = "stripes"
    CHECKS = "checks"
    POLKA_DOT = "polka_dot"
    FLORAL = "floral"
    GEOMETRIC = "geometric"
    ABSTRACT = "abstract"
    ANIMAL_PRINT = "animal_print"


# ============================================
# EMBEDDED DOCUMENTS (BaseModel - not stored separately)
# ============================================

class ColorInfo(BaseModel):
    """Color information for clothing items."""
    name: str = Field(default="", description="Color name")
    hex_code: str = Field(default="#000000", description="Hex color code")
    rgb: List[int] = Field(default=[0, 0, 0], description="RGB values")
    percentage: float = Field(default=0.0, description="Percentage in image")


class SkinFeatures(BaseModel):
    """Embedded skin analysis features."""
    undertone: Optional[Undertone] = None
    depth: Optional[SkinDepth] = None  # Main skin depth field
    skin_depth: Optional[SkinDepth] = None  # Alias for backward compatibility
    season: Optional[Season] = None  # Seasonal color type
    seasonal_type: Optional[Season] = None  # Alias
    lab_l: Optional[float] = Field(None, ge=0, le=100)
    lab_a: Optional[float] = Field(None, ge=-128, le=127)
    lab_b: Optional[float] = Field(None, ge=-128, le=127)
    skin_rgb: List[int] = Field(default_factory=lambda: [0, 0, 0])
    dominant_colors: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class BodyMeasurements(BaseModel):
    """User body measurements."""
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    hip_cm: Optional[float] = None
    body_type: Optional[str] = None  # "hourglass", "pear", "apple", etc.


class StylePreferences(BaseModel):
    """User style preferences."""
    primary_style: Optional[StyleType] = None
    secondary_styles: List[StyleType] = Field(default_factory=list)
    preferred_colors: List[str] = Field(default_factory=list)
    favorite_colors: List[str] = Field(default_factory=list)
    avoided_colors: List[str] = Field(default_factory=list)
    avoid_colors: List[str] = Field(default_factory=list)  # Alias for avoided_colors
    recommended_colors: List[str] = Field(default_factory=list)
    formality_preference: int = Field(default=5, ge=1, le=10)
    occasion_types: List[str] = Field(default_factory=list)


class ClothingFeatures(BaseModel):
    """Clothing item features from analysis."""
    dominant_colors: List[ColorInfo] = Field(default_factory=list)
    design_pattern: DesignPattern = DesignPattern.PLAIN
    category: ClothingCategory = ClothingCategory.UNKNOWN
    weather: WeatherType = WeatherType.ALL_SEASON
    style: StyleType = StyleType.CASUAL
    formality_level: int = Field(default=3, ge=1, le=10)
    fabric_type: Optional[str] = None  # placeholder-quality: not reliable ML output
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    subcategory: Optional[str] = None  # e.g. "t-shirt", "jeans" (category is the coarse group)
    gender: str = "unisex"
    needs_review: bool = False  # classifier was unsure: user should confirm category/style
    user_corrected: bool = False  # fields were edited by the user


class NotificationSettings(BaseModel):
    """User notification preferences."""
    email_notifications: bool = True
    push_notifications: bool = True
    daily_outfit: bool = True
    weather_alerts: bool = True
    event_reminders: bool = True
    style_tips: bool = True


class PrivacySettings(BaseModel):
    """User privacy settings."""
    profile_visibility: str = "private"
    data_sharing: bool = False
    analytics_sharing: bool = True
    marketing_emails: bool = False


class AppearanceSettings(BaseModel):
    """App appearance settings."""
    theme: str = "system"
    language: str = "en"
    compact_mode: bool = False


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of recommendation scores."""
    color_score: float = Field(default=0.0, ge=0, le=1)
    style_score: float = Field(default=0.0, ge=0, le=1)
    formality_score: float = Field(default=0.0, ge=0, le=1)
    confidence_score: float = Field(default=0.0, ge=0, le=1)
    color_reasoning: str = ""
    overall_reasoning: str = ""


# ============================================
# MAIN DOCUMENT MODELS
# ============================================

class User(Document):
    """Main user document - stored in 'users' collection."""
    
    # Basic Info
    email: Indexed(EmailStr, unique=True)
    password_hash: str
    name: str = Field(min_length=1, max_length=100)
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    
    # Account Status
    status: AccountStatus = AccountStatus.ACTIVE
    email_verified: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Onboarding
    onboarding_completed: bool = False
    onboarding_step: int = 0
    
    # OAuth
    google_id: Optional[Indexed(str, unique=True)] = None
    
    # Roles
    roles: List[str] = Field(default_factory=lambda: ["user"])
    
    class Settings:
        name = "users"
        use_state_management = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password_hash": "hashed_password",
                "name": "John Doe",
                "status": "active",
                "roles": ["user"]
            }
        }


class UserProfile(Document):
    """Extended user profile with style data - stored in 'user_profiles' collection."""
    
    user_id: Indexed(PydanticObjectId)
    
    # Physical Characteristics
    skin_features: Optional[SkinFeatures] = None
    body_measurements: Optional[BodyMeasurements] = None
    
    # Style Data
    style_preferences: StylePreferences = Field(default_factory=StylePreferences)
    
    # Profile Images
    avatar_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    selfie_image_url: Optional[str] = None
    
    # Location
    location: Optional[str] = None
    timezone: str = "UTC"
    
    # Style Score
    style_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_profiles"


class UserSettings(Document):
    """User application settings - stored in 'user_settings' collection."""
    
    user_id: Indexed(PydanticObjectId, unique=True)
    
    # Settings
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    appearance: AppearanceSettings = Field(default_factory=AppearanceSettings)
    
    # Two-Factor Authentication
    two_factor_enabled: bool = False
    
    # Google Calendar Integration
    google_calendar_connected: bool = False
    google_calendar_email: Optional[str] = None
    google_access_token: Optional[str] = None
    google_refresh_token: Optional[str] = None
    google_token_expires_at: Optional[datetime] = None
    synced_calendars: List[str] = Field(default_factory=list)
    
    # AI Settings
    ai_personality: str = "friendly"
    ai_verbosity: str = "balanced"
    auto_suggest_outfits: bool = True
    outfit_lead_time_hours: int = 24
    
    # Feature Flags
    beta_features: bool = False
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_settings"


class UserSession(Document):
    """User session tracking - stored in 'user_sessions' collection."""
    
    user_id: Indexed(PydanticObjectId)
    
    # Session Info
    refresh_token: Indexed(str, unique=True)
    
    # Device Info
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    
    # Session State
    is_active: bool = True
    expires_at: datetime
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_sessions"


class ClothingItem(Document):
    """Individual clothing item - stored in 'clothing_items' collection."""
    
    user_id: Indexed(PydanticObjectId)
    
    # Basic Info
    name: str = ""
    brand: Optional[str] = None
    price: Optional[float] = None
    purchase_date: Optional[date] = None
    
    # Images
    image_url: str = ""
    image_path: Optional[str] = None  # server-side file (never exposed directly)
    image_base64: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    # Analysis Results
    features: ClothingFeatures = Field(default_factory=ClothingFeatures)
    analysis_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    is_favorite: bool = False
    
    # Usage Tracking
    times_worn: int = 0
    last_worn: Optional[date] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "clothing_items"


class AnalysisResult(Document):
    """Face/clothing analysis results - stored in 'analysis_results' collection."""
    
    user_id: Optional[Indexed(PydanticObjectId)] = None
    
    # Analysis Type
    analysis_type: Indexed(str)  # "face", "clothing", "outfit"
    
    # Input Data
    image_url: Optional[str] = None
    image_hash: Optional[Indexed(str)] = None
    
    # Results (flexible JSON structure)
    results: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    processing_time_ms: float = 0.0
    
    # Metadata
    model_version: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "analysis_results"


class OutfitRecommendation(Document):
    """Generated outfit recommendations - stored in 'outfit_recommendations' collection."""
    
    user_id: Indexed(PydanticObjectId)
    
    # Recommendation Data
    outfit_name: str = ""
    occasion: Optional[str] = None
    weather_condition: Optional[str] = None
    
    # Clothing Items (references by ID)
    clothing_item_ids: List[PydanticObjectId] = Field(default_factory=list)
    
    # Scores
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    
    # AI Reasoning
    reasoning: Optional[str] = None
    style_tips: List[str] = Field(default_factory=list)
    
    # User Interaction
    is_saved: bool = False
    is_worn: bool = False
    worn_date: Optional[date] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "outfit_recommendations"


class CalendarEvent(Document):
    """Calendar events with outfit planning - stored in 'calendar_events' collection."""
    
    user_id: Indexed(PydanticObjectId)
    
    # Event Info
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    
    # Timing
    start_time: Indexed(datetime)
    end_time: datetime
    timezone: str = "UTC"
    is_all_day: bool = False
    
    # Google Calendar Integration
    google_event_id: Optional[Indexed(str)] = None
    google_calendar_id: Optional[str] = None
    
    # Outfit Planning
    outfit_id: Optional[PydanticObjectId] = None
    weather_data: Optional[Dict[str, Any]] = None
    
    # Event Type
    event_type: Optional[str] = None  # "meeting", "dinner", "casual", etc.
    formality_level: Optional[int] = Field(None, ge=1, le=10)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "calendar_events"


class ChatMessage(Document):
    """AI chat conversation history - stored in 'chat_messages' collection."""
    
    user_id: Indexed(PydanticObjectId)
    
    # Conversation Info
    session_id: Indexed(str)
    message_type: str = "user"  # "user", "assistant", "system"
    
    # Message Content
    message: str
    response: Optional[str] = None
    
    # Context Data
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # AI Model Info
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[float] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "chat_messages"


class OnboardingProgress(Document):
    """User onboarding progress - stored in 'onboarding_progress' collection."""
    
    user_id: Indexed(PydanticObjectId, unique=True)
    
    # Progress
    current_step: str = "selfie"  # "selfie", "body_type", "skin_tone", "style", "complete"
    completed_steps: List[str] = Field(default_factory=list)
    is_complete: bool = False
    
    # Step Data - Generic storage for all steps
    step_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "onboarding_progress"


# ============================================
# MODEL REGISTRY - For Beanie initialization
# ============================================

ALL_MODELS = [
    User,
    UserProfile,
    UserSettings,
    UserSession,
    ClothingItem,
    AnalysisResult,
    OutfitRecommendation,
    CalendarEvent,
    ChatMessage,
    OnboardingProgress,
]
