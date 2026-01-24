# Pydantic schemas for recommendation request/response models
# Author: Recommendation Team
# Last Updated: January 24, 2026

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


# ============================================
# ENUMS FOR TYPE SAFETY
# ============================================

class Undertone(str, Enum):
    """Skin undertone classification"""
    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"


class SkinDepth(str, Enum):
    """Skin depth/darkness level"""
    FAIR = "fair"
    LIGHT = "light"
    MEDIUM = "medium"
    TAN = "tan"
    DEEP = "deep"


class Season(str, Enum):
    """Seasonal color analysis type"""
    SPRING = "spring"  # Warm + Light
    SUMMER = "summer"  # Cool + Light
    AUTUMN = "autumn"  # Warm + Deep
    WINTER = "winter"  # Cool + Deep


class ClothingCategory(str, Enum):
    """Clothing category types"""
    TOP = "top"
    BOTTOM = "bottom"
    DRESS = "dress"
    OUTERWEAR = "outerwear"
    ACCESSORY = "accessory"
    FOOTWEAR = "footwear"


class StyleType(str, Enum):
    """Clothing style classification"""
    CASUAL = "casual"
    FORMAL = "formal"
    BUSINESS = "business"
    SPORTY = "sporty"
    BOHEMIAN = "bohemian"
    VINTAGE = "vintage"
    STREETWEAR = "streetwear"
    MINIMALIST = "minimalist"


class WeatherType(str, Enum):
    """Weather/season suitability"""
    SUMMER = "summer"
    WINTER = "winter"
    SPRING = "spring"
    FALL = "fall"
    ALL_SEASON = "all_season"


class Gender(str, Enum):
    """Gender classification"""
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"


# ============================================
# INPUT SCHEMAS - FROM OTHER MODULES
# ============================================

class SkinFeatures(BaseModel):
    """
    Input from Face Analysis Module
    Contains extracted skin/face features
    
    Integration: Face Analysis team should return this schema
    """
    undertone: Undertone = Field(..., description="Skin undertone: warm, cool, or neutral")
    skin_depth: SkinDepth = Field(..., description="Skin depth level")
    
    # LAB color values from face analysis
    lab_l: float = Field(..., ge=0, le=100, description="LAB Lightness (0-100)")
    lab_a: float = Field(..., ge=-128, le=127, description="LAB A channel (green-red)")
    lab_b: float = Field(..., ge=-128, le=127, description="LAB B channel (blue-yellow)")
    
    # RGB representation
    skin_rgb: List[int] = Field(..., min_length=3, max_length=3, description="RGB skin color [R, G, B]")
    
    # Derived season type
    season: Optional[Season] = Field(None, description="Seasonal color type (auto-calculated if not provided)")
    
    # Confidence from face analysis
    confidence: float = Field(default=1.0, ge=0, le=1, description="Face analysis confidence score")

    class Config:
        json_schema_extra = {
            "example": {
                "undertone": "warm",
                "skin_depth": "medium",
                "lab_l": 65.5,
                "lab_a": 12.3,
                "lab_b": 18.7,
                "skin_rgb": [198, 166, 145],
                "season": "autumn",
                "confidence": 0.92
            }
        }


class ClothFeatures(BaseModel):
    """
    Input from Cloth Analysis Module
    Contains extracted clothing features
    
    Integration: Cloth Analysis team should return this schema
    """
    cloth_id: str = Field(..., description="Unique identifier for the clothing item")
    image_url: Optional[str] = Field(None, description="URL/path to clothing image")
    
    # Color features
    dominant_color_rgb: List[int] = Field(..., min_length=3, max_length=3, description="Dominant color RGB")
    dominant_color_name: str = Field(..., description="Human-readable color name")
    color_palette: List[List[int]] = Field(default=[], description="List of RGB colors in palette")
    color_hex: str = Field(..., description="Hex color code")
    
    # Classification features
    category: ClothingCategory = Field(..., description="Clothing category")
    gender: Gender = Field(..., description="Target gender")
    style: StyleType = Field(..., description="Style classification")
    
    # Pattern/Design
    design: str = Field(..., description="Pattern type: solid, striped, floral, etc.")
    
    # Material
    fabric: str = Field(..., description="Fabric type: cotton, silk, denim, etc.")
    
    # Contextual features
    weather: WeatherType = Field(..., description="Weather suitability")
    formality_level: int = Field(..., ge=1, le=10, description="Formality score 1-10")
    
    # Analysis confidence
    confidence: float = Field(default=1.0, ge=0, le=1, description="Overall extraction confidence")

    class Config:
        json_schema_extra = {
            "example": {
                "cloth_id": "cloth_001",
                "image_url": "/images/blue_shirt.jpg",
                "dominant_color_rgb": [70, 130, 180],
                "dominant_color_name": "steel blue",
                "color_palette": [[70, 130, 180], [100, 149, 237]],
                "color_hex": "#4682B4",
                "category": "top",
                "gender": "unisex",
                "style": "casual",
                "design": "solid",
                "fabric": "cotton",
                "weather": "all_season",
                "formality_level": 4,
                "confidence": 0.88
            }
        }


# ============================================
# USER PREFERENCES
# ============================================

class UserPreferences(BaseModel):
    """User's style and filtering preferences"""
    preferred_styles: List[StyleType] = Field(default=[], description="Preferred style types")
    preferred_colors: List[str] = Field(default=[], description="Preferred color names")
    avoided_colors: List[str] = Field(default=[], description="Colors to avoid")
    
    target_occasion: Optional[str] = Field(None, description="Occasion: casual, work, party, etc.")
    target_weather: Optional[WeatherType] = Field(None, description="Weather/season filter")
    
    gender_filter: Optional[Gender] = Field(None, description="Gender filter")
    category_filter: Optional[List[ClothingCategory]] = Field(None, description="Category filter")
    
    min_formality: int = Field(default=1, ge=1, le=10, description="Minimum formality level")
    max_formality: int = Field(default=10, ge=1, le=10, description="Maximum formality level")
    
    # Scoring weights (sum should ideally be 1.0)
    color_weight: float = Field(default=0.4, ge=0, le=1, description="Weight for color matching")
    style_weight: float = Field(default=0.3, ge=0, le=1, description="Weight for style matching")
    formality_weight: float = Field(default=0.2, ge=0, le=1, description="Weight for formality")
    confidence_weight: float = Field(default=0.1, ge=0, le=1, description="Weight for confidence")

    class Config:
        json_schema_extra = {
            "example": {
                "preferred_styles": ["casual", "minimalist"],
                "preferred_colors": ["blue", "navy", "white"],
                "avoided_colors": ["orange", "yellow"],
                "target_occasion": "work",
                "target_weather": "all_season",
                "gender_filter": "male",
                "category_filter": ["top", "bottom"],
                "min_formality": 3,
                "max_formality": 7,
                "color_weight": 0.4,
                "style_weight": 0.3,
                "formality_weight": 0.2,
                "confidence_weight": 0.1
            }
        }


# ============================================
# REQUEST SCHEMAS
# ============================================

class RecommendationRequest(BaseModel):
    """
    Main recommendation request
    Combines skin features with available clothes and preferences
    """
    skin_features: SkinFeatures = Field(..., description="Extracted skin/face features")
    available_clothes: List[ClothFeatures] = Field(..., description="List of clothing items to rank")
    preferences: Optional[UserPreferences] = Field(default=None, description="User preferences")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of recommendations to return")

    class Config:
        json_schema_extra = {
            "example": {
                "skin_features": {
                    "undertone": "warm",
                    "skin_depth": "medium",
                    "lab_l": 65.5,
                    "lab_a": 12.3,
                    "lab_b": 18.7,
                    "skin_rgb": [198, 166, 145],
                    "confidence": 0.92
                },
                "available_clothes": [],
                "preferences": None,
                "top_k": 10
            }
        }


class SingleClothRecommendationRequest(BaseModel):
    """Request to check compatibility of a single clothing item"""
    skin_features: SkinFeatures = Field(..., description="Extracted skin/face features")
    cloth_features: ClothFeatures = Field(..., description="Single clothing item to evaluate")


class OutfitRecommendationRequest(BaseModel):
    """Request for complete outfit recommendations"""
    skin_features: SkinFeatures = Field(..., description="Extracted skin/face features")
    available_clothes: List[ClothFeatures] = Field(..., description="Available clothing items")
    preferences: Optional[UserPreferences] = Field(default=None, description="User preferences")
    include_categories: List[ClothingCategory] = Field(
        default=[ClothingCategory.TOP, ClothingCategory.BOTTOM],
        description="Categories to include in outfit"
    )


# ============================================
# RESPONSE SCHEMAS
# ============================================

class ScoreBreakdown(BaseModel):
    """Detailed breakdown of recommendation scores"""
    color_score: float = Field(..., ge=0, le=1, description="Color compatibility score")
    style_score: float = Field(..., ge=0, le=1, description="Style preference score")
    formality_score: float = Field(..., ge=0, le=1, description="Formality match score")
    confidence_score: float = Field(..., ge=0, le=1, description="Analysis confidence score")
    
    color_reasoning: str = Field(..., description="Explanation for color score")
    overall_reasoning: str = Field(..., description="Overall recommendation reasoning")


class ClothRecommendation(BaseModel):
    """Single clothing recommendation with scores"""
    cloth_id: str = Field(..., description="Clothing item ID")
    image_url: Optional[str] = Field(None, description="Clothing image URL")
    
    # Scores
    overall_score: float = Field(..., ge=0, le=1, description="Final weighted score")
    score_breakdown: ScoreBreakdown = Field(..., description="Detailed score breakdown")
    
    # Rank
    rank: int = Field(..., ge=1, description="Recommendation rank")
    
    # Original features (for virtual try-on)
    cloth_features: ClothFeatures = Field(..., description="Original clothing features")
    
    # Recommendation quality
    recommendation_level: str = Field(..., description="Highly Recommended, Recommended, Consider, Not Recommended")


class RecommendationResponse(BaseModel):
    """Main recommendation response"""
    success: bool = Field(default=True, description="Request success status")
    
    # User info
    detected_season: Season = Field(..., description="User's seasonal color type")
    undertone: Undertone = Field(..., description="User's undertone")
    skin_depth: SkinDepth = Field(..., description="User's skin depth")
    
    # Recommendations
    recommendations: List[ClothRecommendation] = Field(..., description="Ranked recommendations")
    total_evaluated: int = Field(..., description="Total items evaluated")
    
    # Color guidance
    best_colors: List[str] = Field(..., description="Best colors for this user")
    colors_to_avoid: List[str] = Field(..., description="Colors to avoid")
    
    # Metadata
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class SingleClothRecommendationResponse(BaseModel):
    """Response for single cloth compatibility check"""
    cloth_id: str
    is_recommended: bool
    overall_score: float
    score_breakdown: ScoreBreakdown
    recommendation_level: str
    reasoning: str


class OutfitRecommendation(BaseModel):
    """Complete outfit recommendation"""
    outfit_id: str = Field(..., description="Unique outfit identifier")
    items: List[ClothRecommendation] = Field(..., description="Clothing items in outfit")
    outfit_score: float = Field(..., description="Overall outfit compatibility score")
    outfit_reasoning: str = Field(..., description="Why this outfit works")


class OutfitRecommendationResponse(BaseModel):
    """Response for outfit recommendations"""
    success: bool = True
    outfits: List[OutfitRecommendation]
    detected_season: Season
    undertone: Undertone


# ============================================
# VIRTUAL TRY-ON INTEGRATION SCHEMAS
# ============================================

class TryOnRequest(BaseModel):
    """
    Schema to send to Virtual Try-On module
    Contains recommendation + original images
    
    Integration: Virtual Try-On team should accept this schema
    """
    user_image_url: str = Field(..., description="User's full body image URL")
    recommended_clothes: List[ClothRecommendation] = Field(..., description="Recommended clothes to try on")
    skin_features: SkinFeatures = Field(..., description="User's skin features for reference")
    
    # Options
    try_all: bool = Field(default=False, description="Try all recommended items")
    max_items: int = Field(default=3, description="Maximum items to try on")

    class Config:
        json_schema_extra = {
            "example": {
                "user_image_url": "/images/user_fullbody.jpg",
                "recommended_clothes": [],
                "skin_features": {
                    "undertone": "warm",
                    "skin_depth": "medium",
                    "lab_l": 65.5,
                    "lab_a": 12.3,
                    "lab_b": 18.7,
                    "skin_rgb": [198, 166, 145],
                    "confidence": 0.92
                },
                "try_all": False,
                "max_items": 3
            }
        }


class TryOnResult(BaseModel):
    """Result from virtual try-on for a single item"""
    cloth_id: str
    generated_image_url: str
    fit_score: Optional[float] = None
    processing_time_ms: float


class TryOnResponse(BaseModel):
    """Response from Virtual Try-On module"""
    success: bool
    results: List[TryOnResult]
    total_processing_time_ms: float
