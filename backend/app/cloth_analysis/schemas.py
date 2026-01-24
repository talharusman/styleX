"""
Pydantic schemas for cloth analysis request/response models.
Optimized for 4GB RTX 3050 GPU MVP.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class DesignPattern(str, Enum):
    PLAIN = "plain"
    STRIPES = "stripes"
    CHECKS = "checks"
    POLKA_DOT = "polka_dot"
    FLORAL = "floral"
    GEOMETRIC = "geometric"
    ABSTRACT = "abstract"
    ANIMAL_PRINT = "animal_print"
    CAMO = "camo"
    TIE_DYE = "tie_dye"


class ClothingCategory(str, Enum):
    # Tops
    TSHIRT = "t-shirt"
    SHIRT = "shirt"
    BLOUSE = "blouse"
    SWEATER = "sweater"
    HOODIE = "hoodie"
    TANK_TOP = "tank_top"
    POLO = "polo"
    # Bottoms
    PANTS = "pants"
    JEANS = "jeans"
    SHORTS = "shorts"
    SKIRT = "skirt"
    LEGGINGS = "leggings"
    # Full body
    DRESS = "dress"
    JUMPSUIT = "jumpsuit"
    ROMPER = "romper"
    # Outerwear
    JACKET = "jacket"
    COAT = "coat"
    BLAZER = "blazer"
    CARDIGAN = "cardigan"
    VEST = "vest"
    # Other
    SWIMWEAR = "swimwear"
    ACTIVEWEAR = "activewear"
    UNKNOWN = "unknown"


class WeatherType(str, Enum):
    SUMMER = "summer"
    WINTER = "winter"
    SPRING = "spring"
    FALL = "fall"
    ALL_SEASON = "all_season"


class StyleType(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    BUSINESS = "business"
    SPORTY = "sporty"
    PARTY = "party"
    BOHEMIAN = "bohemian"
    STREETWEAR = "streetwear"
    VINTAGE = "vintage"
    MINIMALIST = "minimalist"


class FabricType(str, Enum):
    COTTON = "cotton"
    SILK = "silk"
    WOOL = "wool"
    POLYESTER = "polyester"
    DENIM = "denim"
    LEATHER = "leather"
    LINEN = "linen"
    VELVET = "velvet"
    UNKNOWN = "unknown"


class ColorInfo(BaseModel):
    """Color information for a clothing item."""
    name: str = Field(..., description="Basic color label (e.g., red, blue, black)")
    hex_code: str = Field(..., description="Hex color code")
    rgb: List[int] = Field(..., description="RGB values [R, G, B]")
    percentage: float = Field(..., description="Percentage of this color in the image")


class ClothInput(BaseModel):
    """Input schema for clothing analysis."""
    image_base64: Optional[str] = Field(None, description="Base64 encoded image")
    image_url: Optional[str] = Field(None, description="URL of the image")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "base64_encoded_string_here",
                "image_url": None
            }
        }


class ClothFeatures(BaseModel):
    """Complete clothing features extracted from analysis."""
    # Color features
    dominant_colors: List[ColorInfo] = Field(default_factory=list, description="List of dominant colors")
    
    # Design pattern
    design_pattern: DesignPattern = Field(DesignPattern.PLAIN, description="Detected design pattern")
    design_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score for design")
    
    # Category classification
    category: ClothingCategory = Field(ClothingCategory.UNKNOWN, description="Clothing category")
    category_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score for category")
    
    # Weather suitability
    weather: WeatherType = Field(WeatherType.ALL_SEASON, description="Weather suitability")
    weather_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence for weather")
    
    # Style classification
    style: StyleType = Field(StyleType.CASUAL, description="Clothing style")
    style_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score for style")
    
    # Fabric (optional for MVP)
    fabric: FabricType = Field(FabricType.UNKNOWN, description="Fabric type (optional)")
    fabric_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence for fabric")
    
    # Formality level (1-5 scale)
    formality_level: int = Field(3, ge=1, le=5, description="Formality level: 1=very casual, 5=very formal")
    formality_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence for formality")
    
    # Overall confidence
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall analysis confidence")


class ClothAnalysisResponse(BaseModel):
    """Response schema for clothing analysis endpoint."""
    success: bool = Field(True, description="Whether analysis was successful")
    features: Optional[ClothFeatures] = Field(None, description="Extracted clothing features")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    processing_time_ms: float = Field(0.0, description="Processing time in milliseconds")
