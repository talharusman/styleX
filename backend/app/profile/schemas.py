"""
Pydantic schemas for Profile endpoints
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class SubscriptionTier(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"


class ProfileVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    FRIENDS = "friends"


class UserProfile(BaseModel):
    """Complete user profile"""
    id: str
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None
    
    # Personal info
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    location: Optional[str] = None
    timezone: str = "UTC"
    
    # Style profile
    body_type: Optional[str] = None
    skin_tone: Optional[str] = None
    undertone: Optional[str] = None
    seasonal_type: Optional[str] = None
    primary_style: Optional[str] = None
    secondary_styles: List[str] = Field(default_factory=list)
    
    # Measurements (optional)
    height: Optional[float] = Field(default=None, description="Height in cm")
    weight: Optional[float] = Field(default=None, description="Weight in kg")
    chest: Optional[float] = None
    waist: Optional[float] = None
    hips: Optional[float] = None
    
    # Color preferences
    favorite_colors: List[str] = Field(default_factory=list)
    avoid_colors: List[str] = Field(default_factory=list)
    recommended_colors: List[str] = Field(default_factory=list)
    
    # Subscription & status
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    subscription_expires: Optional[datetime] = None
    
    # Onboarding status
    onboarding_complete: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # Privacy
    visibility: ProfileVisibility = ProfileVisibility.PRIVATE


class ProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    name: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    
    # Style updates
    body_type: Optional[str] = None
    skin_tone: Optional[str] = None
    undertone: Optional[str] = None
    primary_style: Optional[str] = None
    secondary_styles: Optional[List[str]] = None
    
    # Measurements
    height: Optional[float] = None
    weight: Optional[float] = None
    chest: Optional[float] = None
    waist: Optional[float] = None
    hips: Optional[float] = None
    
    # Color preferences
    favorite_colors: Optional[List[str]] = None
    avoid_colors: Optional[List[str]] = None
    
    # Privacy
    visibility: Optional[ProfileVisibility] = None


class StyleProfile(BaseModel):
    """User's style profile extracted from main profile"""
    user_id: str
    body_type: Optional[str] = None
    skin_tone: Optional[str] = None
    undertone: Optional[str] = None
    seasonal_type: Optional[str] = None
    primary_style: Optional[str] = None
    secondary_styles: List[str] = Field(default_factory=list)
    favorite_colors: List[str] = Field(default_factory=list)
    avoid_colors: List[str] = Field(default_factory=list)
    recommended_colors: List[str] = Field(default_factory=list)


class ProfileStats(BaseModel):
    """User profile statistics"""
    user_id: str
    outfits_created: int = 0
    outfits_favorited: int = 0
    wardrobe_items: int = 0
    events_synced: int = 0
    ai_chats: int = 0
    style_score: Optional[float] = None
    member_since: Optional[datetime] = None
    days_active: int = 0


class AvatarUpload(BaseModel):
    """Avatar upload request"""
    image_base64: Optional[str] = None
    image_url: Optional[str] = None


class ProfileSummary(BaseModel):
    """Compact profile summary for display"""
    id: str
    name: str
    avatar_url: Optional[str] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    style_summary: str = ""
    location: Optional[str] = None
