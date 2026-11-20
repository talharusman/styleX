"""
Face Analysis Schemas

Pydantic models for face analysis request/response.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class SkinUndertone(str, Enum):
    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"


class SkinDepth(str, Enum):
    FAIR = "fair"
    LIGHT = "light"
    MEDIUM = "medium"
    TAN = "tan"
    DEEP = "deep"


class SeasonalType(str, Enum):
    SPRING = "spring"  # Warm + Light
    SUMMER = "summer"  # Cool + Light
    AUTUMN = "autumn"  # Warm + Deep
    WINTER = "winter"  # Cool + Deep


class FaceShape(str, Enum):
    OVAL = "oval"
    ROUND = "round"
    SQUARE = "square"
    HEART = "heart"
    OBLONG = "oblong"
    DIAMOND = "diamond"


class FaceAnalysisInput(BaseModel):
    """Input for face analysis"""
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64 encoded image of face"
    )
    image_url: Optional[str] = Field(
        default=None,
        description="URL of face image"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
            }
        }


class SkinFeatures(BaseModel):
    """Extracted skin features from face analysis"""
    undertone: SkinUndertone = Field(
        description="Skin undertone (warm, cool, neutral)"
    )
    skin_depth: SkinDepth = Field(
        description="Skin depth classification"
    )
    seasonal_type: SeasonalType = Field(
        description="Seasonal color analysis type"
    )
    lab_l: float = Field(
        ge=0, le=100,
        description="LAB color space L (lightness) value"
    )
    lab_a: float = Field(
        description="LAB color space A (green-red) value"
    )
    lab_b: float = Field(
        description="LAB color space B (blue-yellow) value"
    )
    skin_rgb: List[int] = Field(
        min_length=3, max_length=3,
        description="Average skin color as RGB"
    )
    skin_hex: str = Field(
        description="Average skin color as hex"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Confidence score for skin analysis"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "undertone": "warm",
                "skin_depth": "medium",
                "seasonal_type": "autumn",
                "lab_l": 65.0,
                "lab_a": 12.0,
                "lab_b": 18.0,
                "skin_rgb": [198, 166, 145],
                "skin_hex": "#C6A691",
                "confidence": 0.92
            }
        }


class FacialFeatures(BaseModel):
    """Facial structure features"""
    face_shape: FaceShape = Field(
        description="Detected face shape"
    )
    face_width: float = Field(
        description="Face width in pixels"
    )
    face_height: float = Field(
        description="Face height in pixels"
    )
    eye_distance: float = Field(
        description="Distance between eyes in pixels"
    )
    jawline_angle: float = Field(
        description="Jawline angle in degrees"
    )
    forehead_ratio: float = Field(
        description="Forehead height ratio"
    )
    confidence: float = Field(
        ge=0, le=1,
        description="Confidence score for face shape detection"
    )


class ColorRecommendations(BaseModel):
    """Color recommendations based on skin analysis"""
    best_colors: List[str] = Field(
        description="Colors that complement skin tone"
    )
    avoid_colors: List[str] = Field(
        description="Colors to avoid"
    )
    neutral_colors: List[str] = Field(
        description="Safe neutral choices"
    )
    accent_colors: List[str] = Field(
        description="Good accent/pop colors"
    )
    metals: List[str] = Field(
        description="Recommended metal accessories"
    )


class FaceAnalysisResponse(BaseModel):
    """Complete face analysis response"""
    success: bool = True
    skin_features: SkinFeatures
    facial_features: Optional[FacialFeatures] = None
    color_recommendations: ColorRecommendations
    style_tips: List[str] = Field(
        default_factory=list,
        description="Personalized style tips"
    )
    processing_time_ms: float = Field(
        description="Processing time in milliseconds"
    )
    error: Optional[str] = None
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable failure reason: no_face_detected, insufficient_skin_pixels, invalid_image, analyzer_unavailable"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "skin_features": {
                    "undertone": "warm",
                    "skin_depth": "medium",
                    "seasonal_type": "autumn",
                    "lab_l": 65.0,
                    "lab_a": 12.0,
                    "lab_b": 18.0,
                    "skin_rgb": [198, 166, 145],
                    "skin_hex": "#C6A691",
                    "confidence": 0.92
                },
                "color_recommendations": {
                    "best_colors": ["olive", "burnt orange", "warm brown", "coral"],
                    "avoid_colors": ["pink", "light blue", "silver"],
                    "neutral_colors": ["cream", "camel", "warm gray"],
                    "accent_colors": ["gold", "terracotta", "rust"],
                    "metals": ["gold", "brass", "copper"]
                },
                "style_tips": [
                    "Warm earthy tones enhance your complexion",
                    "Avoid cool pastels which may wash you out"
                ],
                "processing_time_ms": 245.5
            }
        }
