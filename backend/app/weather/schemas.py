"""
Pydantic schemas for Weather API endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class WeatherCondition(str, Enum):
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    PARTLY_CLOUDY = "partly_cloudy"
    RAINY = "rainy"
    STORMY = "stormy"
    SNOWY = "snowy"
    WINDY = "windy"
    FOGGY = "foggy"
    HOT = "hot"
    COLD = "cold"


class TemperatureUnit(str, Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


class WeatherRequest(BaseModel):
    """Request schema for weather endpoint"""
    location: str = Field(..., description="City name or coordinates")
    units: TemperatureUnit = Field(
        default=TemperatureUnit.CELSIUS,
        description="Temperature unit"
    )


class WeatherData(BaseModel):
    """Current weather data"""
    location: str
    temperature: float
    feels_like: float
    condition: str
    description: str
    humidity: int
    wind_speed: float
    wind_direction: Optional[str] = None
    visibility: Optional[float] = None
    pressure: Optional[float] = None
    uv_index: Optional[float] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    icon: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OutfitSuggestion(BaseModel):
    """Outfit suggestion based on weather"""
    category: str = Field(..., description="Type of outfit suggestion")
    items: List[str] = Field(..., description="Suggested clothing items")
    reason: str = Field(..., description="Why this outfit is recommended")
    priority: int = Field(default=1, description="Priority level 1-5")


class WeatherResponse(BaseModel):
    """Response schema for weather endpoint with outfit suggestions"""
    weather: WeatherData
    outfit_suggestions: List[OutfitSuggestion]
    weather_advice: str = Field(..., description="General weather-based advice")
    recommended_colors: List[str] = Field(
        default_factory=list,
        description="Recommended colors for the weather"
    )


class ForecastDay(BaseModel):
    """Single day forecast"""
    date: str
    day_of_week: str
    high_temp: float
    low_temp: float
    condition: str
    description: str
    icon: Optional[str] = None
    precipitation_chance: Optional[int] = None


class ForecastResponse(BaseModel):
    """Multi-day forecast response"""
    location: str
    forecast: List[ForecastDay]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class LocationSearchResult(BaseModel):
    """Location search result"""
    name: str
    country: str
    state: Optional[str] = None
    lat: float
    lon: float
