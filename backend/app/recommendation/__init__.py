# Recommendation Engine Module
# Author: Recommendation Team
# Last Updated: January 24, 2026
#
# Matches clothing with skin tone and undertone using color theory,
# seasonal analysis, and user preferences.

from .schemas import (
    # Enums
    Undertone, SkinDepth, Season, ClothingCategory, 
    StyleType, WeatherType, Gender,
    
    # Input schemas
    SkinFeatures, ClothFeatures, UserPreferences,
    
    # Request schemas
    RecommendationRequest, SingleClothRecommendationRequest,
    OutfitRecommendationRequest,
    
    # Response schemas
    RecommendationResponse, SingleClothRecommendationResponse,
    OutfitRecommendationResponse, ClothRecommendation,
    ScoreBreakdown, OutfitRecommendation,
    
    # Virtual Try-On integration
    TryOnRequest, TryOnResponse, TryOnResult,
)

from .service import RecommendationService, get_recommendation_service
from .router import router

__all__ = [
    # Enums
    "Undertone", "SkinDepth", "Season", "ClothingCategory",
    "StyleType", "WeatherType", "Gender",
    
    # Schemas
    "SkinFeatures", "ClothFeatures", "UserPreferences",
    "RecommendationRequest", "RecommendationResponse",
    "SingleClothRecommendationRequest", "SingleClothRecommendationResponse",
    "OutfitRecommendationRequest", "OutfitRecommendationResponse",
    "ClothRecommendation", "ScoreBreakdown", "OutfitRecommendation",
    "TryOnRequest", "TryOnResponse", "TryOnResult",
    
    # Service
    "RecommendationService", "get_recommendation_service",
    
    # Router
    "router",
]
