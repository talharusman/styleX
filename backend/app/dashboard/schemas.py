"""
Pydantic schemas for Dashboard endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class WeatherWidget(BaseModel):
    """Weather widget data for dashboard"""
    location: str
    temperature: float
    condition: str
    description: str
    humidity: int
    icon: Optional[str] = None
    outfit_advice: str = ""
    recommended_colors: List[str] = Field(default_factory=list)


class EventWidget(BaseModel):
    """Calendar event widget for dashboard"""
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_today: bool = False
    outfit_suggestion: Optional[str] = None
    time_until: Optional[str] = None


class OutfitCard(BaseModel):
    """Single outfit recommendation card"""
    id: str
    title: str
    description: str
    occasion: str
    items: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    style_tags: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    is_weather_appropriate: bool = True
    is_event_appropriate: bool = True


class OutfitCarousel(BaseModel):
    """Outfit carousel for dashboard"""
    outfits: List[OutfitCard] = Field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 5


class UserStats(BaseModel):
    """User statistics for dashboard"""
    total_outfits_viewed: int = 0
    favorites_count: int = 0
    wardrobe_items: int = 0
    events_this_week: int = 0
    style_score: Optional[float] = None


class QuickAction(BaseModel):
    """Quick action button for dashboard"""
    id: str
    label: str
    icon: str
    action_type: str
    destination: str


class DashboardData(BaseModel):
    """Complete dashboard data"""
    user_id: str
    user_name: Optional[str] = None
    greeting: str = "Welcome back!"
    current_date: date = Field(default_factory=date.today)
    
    # Widgets
    weather: Optional[WeatherWidget] = None
    upcoming_events: List[EventWidget] = Field(default_factory=list)
    outfit_carousel: OutfitCarousel = Field(default_factory=OutfitCarousel)
    
    # Additional data
    stats: Optional[UserStats] = None
    quick_actions: List[QuickAction] = Field(default_factory=list)
    notifications: List[dict] = Field(default_factory=list)
    
    # Personalization
    outfit_of_the_day: Optional[OutfitCard] = None
    style_tip: Optional[str] = None
    
    # Timestamps
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    cache_expires_at: Optional[datetime] = None


class DashboardRequest(BaseModel):
    """Request for dashboard data"""
    user_id: str
    location: Optional[str] = Field(default=None, description="Location for weather")
    include_weather: bool = True
    include_events: bool = True
    include_outfits: bool = True
    outfit_count: int = Field(default=5, ge=1, le=20)
    event_hours_ahead: int = Field(default=24, ge=1, le=168)


class OutfitOfTheDayRequest(BaseModel):
    """Request for outfit of the day"""
    user_id: str
    location: Optional[str] = None
    occasion: Optional[str] = None
    date: Optional[date] = None
