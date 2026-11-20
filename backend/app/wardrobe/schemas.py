"""Wardrobe API schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PrimaryColor(BaseModel):
    name: str
    hex_code: str
    rgb: List[int]


class WardrobeItem(BaseModel):
    id: str
    name: str
    image_url: str = Field(description="API path to the (authenticated) image endpoint")
    category: str = Field(description="top, bottom, dress, outerwear, accessory, footwear or unknown")
    subcategory: Optional[str] = None
    style: str
    formality_level: int = Field(ge=1, le=10)
    weather: str
    pattern: str
    gender: str
    fabric: Optional[str] = Field(
        default=None,
        description="Placeholder-quality guess; not reliable fabric detection"
    )
    primary_color: PrimaryColor
    colors: List[PrimaryColor] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    needs_review: bool = Field(description="The classifier was unsure; confirm category and style")
    user_corrected: bool = False
    is_favorite: bool = False
    tags: List[str] = Field(default_factory=list)
    created_at: datetime


class WardrobeItemList(BaseModel):
    success: bool = True
    items: List[WardrobeItem]
    total: int


class WardrobeItemUpdate(BaseModel):
    """Fields a user may correct after analysis."""
    name: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(
        default=None, pattern="^(top|bottom|dress|outerwear|accessory|footwear)$"
    )
    style: Optional[str] = Field(
        default=None,
        pattern="^(casual|formal|business|sporty|bohemian|vintage|streetwear|minimalist|party)$"
    )
    formality_level: Optional[int] = Field(default=None, ge=1, le=10)
    primary_color_name: Optional[str] = Field(default=None, max_length=40)
    primary_color_hex: Optional[str] = Field(default=None, pattern="^#[0-9a-fA-F]{6}$")
    tags: Optional[List[str]] = Field(default=None, max_length=20)


class RankedItem(BaseModel):
    rank: int
    item: WardrobeItem
    overall_score: float = Field(ge=0, le=1)
    recommendation_level: str
    color_score: float
    style_score: float
    formality_score: float
    confidence_score: float
    reasoning: str


class WardrobeRecommendations(BaseModel):
    success: bool = True
    detected_season: Optional[str] = None
    undertone: Optional[str] = None
    best_colors: List[str] = Field(default_factory=list)
    colors_to_avoid: List[str] = Field(default_factory=list)
    recommendations: List[RankedItem] = Field(default_factory=list)
    total_evaluated: int = 0
    excluded_needs_review: int = Field(
        default=0, description="Items without a confirmed category are not ranked"
    )
    reason: Optional[str] = Field(
        default=None, description="Why the list is empty, e.g. empty_wardrobe"
    )


class OutfitView(BaseModel):
    outfit_id: str
    items: List[RankedItem]
    outfit_score: float
    reasoning: str


class OutfitSuggestions(BaseModel):
    success: bool = True
    outfits: List[OutfitView] = Field(default_factory=list)
    reason: Optional[str] = Field(
        default=None, description="Why there are no outfits, e.g. need_top_and_bottom"
    )


class SaveOutfitRequest(BaseModel):
    name: str = Field(default="My outfit", max_length=100)
    item_ids: List[str] = Field(min_length=2, max_length=8)
    score: float = Field(default=0.0, ge=0, le=1)
    reasoning: Optional[str] = Field(default=None, max_length=1000)
    occasion: Optional[str] = Field(default=None, max_length=60)


class SavedOutfit(BaseModel):
    id: str
    name: str
    items: List[WardrobeItem]
    score: float
    reasoning: Optional[str] = None
    occasion: Optional[str] = None
    created_at: datetime


class SavedOutfitList(BaseModel):
    success: bool = True
    outfits: List[SavedOutfit]
