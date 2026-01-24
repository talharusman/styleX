"""
Database Module

MongoDB database connection, models, and repositories for StyleX.
"""

from .connection import (
    connect_to_database,
    disconnect_from_database,
    get_database,
    get_client,
    check_database_health,
)
from .models import (
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
    # Embedded models
    SkinFeatures,
    BodyMeasurements,
    StylePreferences,
    ClothingFeatures,
    ColorInfo,
    NotificationSettings,
    PrivacySettings,
    AppearanceSettings,
    ScoreBreakdown,
    # Enums
    Gender,
    AccountStatus,
    Undertone,
    SkinDepth,
    Season,
    ClothingCategory,
    StyleType,
    WeatherType,
    DesignPattern,
)
from .repositories import (
    user_repository,
    get_user_repository,
    clothing_repository,
    get_clothing_repository,
    chat_repository,
    get_chat_repository,
    hash_password,
    verify_password,
)

__all__ = [
    # Connection
    "connect_to_database",
    "disconnect_from_database",
    "get_database",
    "get_client",
    "check_database_health",
    # Models
    "User",
    "UserProfile",
    "UserSettings",
    "UserSession",
    "ClothingItem",
    "AnalysisResult",
    "OutfitRecommendation",
    "CalendarEvent",
    "ChatMessage",
    "OnboardingProgress",
    # Embedded
    "SkinFeatures",
    "BodyMeasurements",
    "StylePreferences",
    "ClothingFeatures",
    "ColorInfo",
    "NotificationSettings",
    "PrivacySettings",
    "AppearanceSettings",
    "ScoreBreakdown",
    # Enums
    "Gender",
    "AccountStatus",
    "Undertone",
    "SkinDepth",
    "Season",
    "ClothingCategory",
    "StyleType",
    "WeatherType",
    "DesignPattern",
    # Repositories
    "user_repository",
    "get_user_repository",
    "clothing_repository",
    "get_clothing_repository",
    "chat_repository",
    "get_chat_repository",
    "hash_password",
    "verify_password",
]
