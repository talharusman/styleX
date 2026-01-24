"""
Pydantic schemas for Onboarding endpoints
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OnboardingStep(str, Enum):
    SELFIE = "selfie"
    BODY_TYPE = "body_type"
    SKIN_TONE = "skin_tone"
    STYLE = "style"
    COMPLETE = "complete"


class BodyType(str, Enum):
    ECTOMORPH = "ectomorph"  # Lean and long
    MESOMORPH = "mesomorph"  # Muscular and well-built
    ENDOMORPH = "endomorph"  # Big, high body fat
    RECTANGLE = "rectangle"  # Similar measurements throughout
    TRIANGLE = "triangle"  # Wider hips than shoulders
    INVERTED_TRIANGLE = "inverted_triangle"  # Wider shoulders than hips
    HOURGLASS = "hourglass"  # Balanced with defined waist
    OVAL = "oval"  # Fuller midsection
    ATHLETIC = "athletic"  # Muscular, defined


class SkinTone(str, Enum):
    FAIR = "fair"
    LIGHT = "light"
    MEDIUM = "medium"
    OLIVE = "olive"
    TAN = "tan"
    BROWN = "brown"
    DARK = "dark"


class SkinUndertone(str, Enum):
    WARM = "warm"  # Yellow, peachy, golden
    COOL = "cool"  # Pink, red, blue
    NEUTRAL = "neutral"  # Mix of warm and cool


class StylePreference(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    BUSINESS_CASUAL = "business_casual"
    STREETWEAR = "streetwear"
    MINIMALIST = "minimalist"
    BOHEMIAN = "bohemian"
    CLASSIC = "classic"
    TRENDY = "trendy"
    SPORTY = "sporty"
    VINTAGE = "vintage"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


# Step-specific schemas
class SelfieStepData(BaseModel):
    """Data from selfie analysis step"""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    face_shape: Optional[str] = None
    skin_tone_detected: Optional[SkinTone] = None
    undertone_detected: Optional[SkinUndertone] = None
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    analysis_confidence: Optional[float] = None


class BodyTypeStepData(BaseModel):
    """Data from body type step"""
    body_type: BodyType
    height: Optional[float] = Field(default=None, description="Height in cm")
    weight: Optional[float] = Field(default=None, description="Weight in kg")
    chest: Optional[float] = Field(default=None, description="Chest measurement in cm")
    waist: Optional[float] = Field(default=None, description="Waist measurement in cm")
    hips: Optional[float] = Field(default=None, description="Hip measurement in cm")
    gender: Optional[Gender] = None


class SkinToneStepData(BaseModel):
    """Data from skin tone step"""
    skin_tone: SkinTone
    undertone: SkinUndertone
    confirmed_by_user: bool = True
    seasonal_color_type: Optional[str] = Field(
        default=None,
        description="Spring, Summer, Autumn, Winter"
    )


class StyleStepData(BaseModel):
    """Data from style preference step"""
    primary_style: StylePreference
    secondary_styles: List[StylePreference] = Field(default_factory=list)
    favorite_colors: List[str] = Field(default_factory=list)
    avoid_colors: List[str] = Field(default_factory=list)
    occasions: List[str] = Field(
        default_factory=list,
        description="Common occasions: work, casual, formal, date, etc."
    )
    budget_range: Optional[str] = Field(
        default=None,
        description="Budget preference: budget, moderate, premium, luxury"
    )
    favorite_brands: List[str] = Field(default_factory=list)


class CompleteStepData(BaseModel):
    """Data for completing onboarding"""
    terms_accepted: bool = True
    notifications_enabled: bool = True
    marketing_emails: bool = False
    timezone: str = "UTC"
    preferred_units: str = "metric"  # metric or imperial


# Request/Response schemas
class OnboardingStepRequest(BaseModel):
    """Request to update a specific onboarding step"""
    step: OnboardingStep
    data: dict = Field(..., description="Step-specific data")


class OnboardingProgress(BaseModel):
    """User's onboarding progress"""
    user_id: str
    current_step: OnboardingStep
    completed_steps: List[OnboardingStep] = Field(default_factory=list)
    step_data: dict = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    is_complete: bool = False


class OnboardingStepResponse(BaseModel):
    """Response after updating an onboarding step"""
    success: bool
    step: OnboardingStep
    next_step: Optional[OnboardingStep] = None
    progress_percentage: float
    message: str


class OnboardingSummary(BaseModel):
    """Summary of completed onboarding"""
    user_id: str
    body_type: Optional[BodyType] = None
    skin_tone: Optional[SkinTone] = None
    undertone: Optional[SkinUndertone] = None
    seasonal_type: Optional[str] = None
    primary_style: Optional[StylePreference] = None
    secondary_styles: List[StylePreference] = Field(default_factory=list)
    favorite_colors: List[str] = Field(default_factory=list)
    recommended_colors: List[str] = Field(default_factory=list)
    avoid_colors: List[str] = Field(default_factory=list)
    face_shape: Optional[str] = None
    gender: Optional[Gender] = None


class AnalyzeSelfieRequest(BaseModel):
    """Request to analyze a selfie"""
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image")
    image_url: Optional[str] = Field(default=None, description="URL to image")


class AnalyzeSelfieResponse(BaseModel):
    """Response from selfie analysis"""
    success: bool
    face_detected: bool
    face_shape: Optional[str] = None
    skin_tone: Optional[SkinTone] = None
    undertone: Optional[SkinUndertone] = None
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    confidence: float = 0.0
    message: str = ""
