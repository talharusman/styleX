"""
Weather Service - Handles weather API calls and outfit suggestions
"""

import os
import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .schemas import (
    WeatherData,
    OutfitSuggestion,
    WeatherResponse,
    ForecastDay,
    ForecastResponse,
    LocationSearchResult,
    TemperatureUnit
)

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data and generating outfit suggestions"""
    
    # OpenWeatherMap API configuration
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    GEO_URL = "https://api.openweathermap.org/geo/1.0"
    
    # Weather-based outfit rules
    OUTFIT_RULES = {
        "hot": {
            "temp_range": (30, 100),
            "items": ["lightweight cotton shirts", "shorts", "sundresses", "sandals", "sunglasses", "sun hat"],
            "colors": ["white", "beige", "light blue", "pastel pink", "light gray"],
            "avoid": ["dark colors", "heavy fabrics", "layered outfits"]
        },
        "warm": {
            "temp_range": (20, 30),
            "items": ["t-shirts", "light jeans", "cotton pants", "sneakers", "light cardigan"],
            "colors": ["light blue", "coral", "mint", "lavender", "cream"],
            "avoid": ["heavy jackets", "thick sweaters"]
        },
        "mild": {
            "temp_range": (15, 20),
            "items": ["long-sleeve shirts", "jeans", "light sweater", "blazer", "loafers"],
            "colors": ["navy", "burgundy", "olive", "camel", "rust"],
            "avoid": ["tank tops", "heavy winter wear"]
        },
        "cool": {
            "temp_range": (10, 15),
            "items": ["sweaters", "jackets", "jeans", "boots", "scarves"],
            "colors": ["charcoal", "forest green", "maroon", "mustard", "chocolate"],
            "avoid": ["shorts", "sandals", "thin fabrics"]
        },
        "cold": {
            "temp_range": (-10, 10),
            "items": ["heavy coat", "wool sweater", "thermal layers", "boots", "gloves", "beanie", "scarf"],
            "colors": ["black", "deep navy", "burgundy", "forest green", "charcoal"],
            "avoid": ["thin layers", "exposed skin", "cotton socks"]
        },
        "rainy": {
            "items": ["waterproof jacket", "rain boots", "umbrella", "water-resistant pants"],
            "colors": ["navy", "hunter green", "black", "yellow", "red"],
            "avoid": ["suede shoes", "leather without protection", "white fabrics"]
        },
        "snowy": {
            "items": ["insulated coat", "waterproof boots", "thermal underwear", "gloves", "wool hat", "scarf"],
            "colors": ["red", "emerald", "black", "cream", "camel"],
            "avoid": ["thin soles", "cotton layers", "short pants"]
        },
        "windy": {
            "items": ["windbreaker", "fitted clothes", "secured accessories"],
            "colors": ["any"],
            "avoid": ["loose fabrics", "wide-brimmed hats", "flowy dresses"]
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Weather service
        
        Args:
            api_key: OpenWeatherMap API key. Uses env variable if not provided.
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY", "")
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured. Weather features will be limited.")
    
    async def get_weather(
        self,
        location: str,
        units: TemperatureUnit = TemperatureUnit.CELSIUS
    ) -> WeatherResponse:
        """
        Get current weather for a location with outfit suggestions
        
        Args:
            location: City name or coordinates
            units: Temperature unit
            
        Returns:
            WeatherResponse with weather data and outfit suggestions
        """
        weather_data = await self._fetch_weather(location, units)
        outfit_suggestions = self._generate_outfit_suggestions(weather_data)
        weather_advice = self._generate_weather_advice(weather_data)
        recommended_colors = self._get_recommended_colors(weather_data)
        
        return WeatherResponse(
            weather=weather_data,
            outfit_suggestions=outfit_suggestions,
            weather_advice=weather_advice,
            recommended_colors=recommended_colors
        )
    
    async def _fetch_weather(
        self,
        location: str,
        units: TemperatureUnit
    ) -> WeatherData:
        """Fetch current weather from OpenWeatherMap API"""
        
        if not self.api_key:
            # Return mock data if no API key
            return self._get_mock_weather(location)
        
        try:
            unit_param = "metric" if units == TemperatureUnit.CELSIUS else "imperial"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/weather",
                    params={
                        "q": location,
                        "appid": self.api_key,
                        "units": unit_param
                    }
                )
                
                if response.status_code == 404:
                    raise ValueError(f"Location '{location}' not found")
                
                response.raise_for_status()
                data = response.json()
                
                return WeatherData(
                    location=f"{data['name']}, {data.get('sys', {}).get('country', '')}",
                    temperature=data['main']['temp'],
                    feels_like=data['main']['feels_like'],
                    condition=data['weather'][0]['main'],
                    description=data['weather'][0]['description'],
                    humidity=data['main']['humidity'],
                    wind_speed=data['wind']['speed'],
                    wind_direction=self._get_wind_direction(data['wind'].get('deg', 0)),
                    visibility=data.get('visibility', 10000) / 1000,  # Convert to km
                    pressure=data['main']['pressure'],
                    icon=data['weather'][0]['icon'],
                    sunrise=datetime.fromtimestamp(data['sys']['sunrise']).strftime("%H:%M"),
                    sunset=datetime.fromtimestamp(data['sys']['sunset']).strftime("%H:%M")
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching weather: {str(e)}")
            return self._get_mock_weather(location)
        except Exception as e:
            logger.error(f"Error fetching weather: {str(e)}")
            return self._get_mock_weather(location)
    
    def _get_mock_weather(self, location: str) -> WeatherData:
        """Return mock weather data for development/testing"""
        return WeatherData(
            location=location,
            temperature=22.0,
            feels_like=23.0,
            condition="Clear",
            description="clear sky",
            humidity=45,
            wind_speed=3.5,
            wind_direction="NE",
            visibility=10.0,
            pressure=1013.0,
            sunrise="06:30",
            sunset="18:45"
        )
    
    def _get_wind_direction(self, degrees: int) -> str:
        """Convert wind degrees to cardinal direction"""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(degrees / 45) % 8
        return directions[index]
    
    def _generate_outfit_suggestions(self, weather: WeatherData) -> List[OutfitSuggestion]:
        """Generate outfit suggestions based on weather conditions"""
        suggestions = []
        temp = weather.temperature
        condition = weather.condition.lower()
        
        # Determine temperature category
        temp_category = self._get_temp_category(temp)
        
        # Base outfit for temperature
        if temp_category in self.OUTFIT_RULES:
            rules = self.OUTFIT_RULES[temp_category]
            suggestions.append(OutfitSuggestion(
                category="Temperature-Based",
                items=rules["items"],
                reason=f"Based on {temp}° temperature, these items will keep you comfortable",
                priority=1
            ))
        
        # Weather condition adjustments
        if "rain" in condition or "drizzle" in condition:
            rain_rules = self.OUTFIT_RULES["rainy"]
            suggestions.append(OutfitSuggestion(
                category="Rain Protection",
                items=rain_rules["items"],
                reason="Rain is expected - stay dry with waterproof options",
                priority=2
            ))
        
        if "snow" in condition:
            snow_rules = self.OUTFIT_RULES["snowy"]
            suggestions.append(OutfitSuggestion(
                category="Snow Gear",
                items=snow_rules["items"],
                reason="Snow conditions require warm, waterproof layers",
                priority=1
            ))
        
        # Wind consideration
        if weather.wind_speed > 10:
            wind_rules = self.OUTFIT_RULES["windy"]
            suggestions.append(OutfitSuggestion(
                category="Wind Protection",
                items=wind_rules["items"],
                reason=f"High winds ({weather.wind_speed} m/s) - wear fitted, secured clothing",
                priority=3
            ))
        
        # UV/Sun consideration
        if weather.uv_index and weather.uv_index > 6:
            suggestions.append(OutfitSuggestion(
                category="Sun Protection",
                items=["sunglasses", "sun hat", "SPF clothing", "light long sleeves"],
                reason=f"High UV index ({weather.uv_index}) - protect your skin",
                priority=2
            ))
        
        return suggestions
    
    def _get_temp_category(self, temp: float) -> str:
        """Determine temperature category"""
        if temp >= 30:
            return "hot"
        elif temp >= 20:
            return "warm"
        elif temp >= 15:
            return "mild"
        elif temp >= 10:
            return "cool"
        else:
            return "cold"
    
    def _generate_weather_advice(self, weather: WeatherData) -> str:
        """Generate general weather advice"""
        temp = weather.temperature
        condition = weather.condition.lower()
        
        advice_parts = []
        
        # Temperature advice
        if temp >= 30:
            advice_parts.append("It's hot outside! Stay hydrated and wear breathable fabrics.")
        elif temp >= 20:
            advice_parts.append("Pleasant weather for outdoor activities.")
        elif temp >= 10:
            advice_parts.append("Layer up - it's cool outside.")
        else:
            advice_parts.append("Bundle up warmly - it's cold!")
        
        # Condition-specific advice
        if "rain" in condition:
            advice_parts.append("Carry an umbrella and wear waterproof shoes.")
        elif "snow" in condition:
            advice_parts.append("Watch for slippery surfaces and dress in layers.")
        elif "clear" in condition or "sunny" in condition:
            advice_parts.append("Great visibility - perfect for your planned activities.")
        elif "cloud" in condition:
            advice_parts.append("Overcast skies - layers are a good idea.")
        
        # Humidity advice
        if weather.humidity > 70:
            advice_parts.append("High humidity - choose moisture-wicking fabrics.")
        
        return " ".join(advice_parts)
    
    def _get_recommended_colors(self, weather: WeatherData) -> List[str]:
        """Get recommended colors based on weather"""
        temp_category = self._get_temp_category(weather.temperature)
        
        if temp_category in self.OUTFIT_RULES:
            return self.OUTFIT_RULES[temp_category].get("colors", [])
        
        return ["navy", "black", "gray", "white", "beige"]
    
    async def get_forecast(
        self,
        location: str,
        days: int = 5,
        units: TemperatureUnit = TemperatureUnit.CELSIUS
    ) -> ForecastResponse:
        """
        Get weather forecast for multiple days
        
        Args:
            location: City name or coordinates
            days: Number of days (max 5 for free tier)
            units: Temperature unit
            
        Returns:
            ForecastResponse with daily forecasts
        """
        if not self.api_key:
            return self._get_mock_forecast(location, days)
        
        try:
            unit_param = "metric" if units == TemperatureUnit.CELSIUS else "imperial"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/forecast",
                    params={
                        "q": location,
                        "appid": self.api_key,
                        "units": unit_param,
                        "cnt": days * 8  # 8 intervals per day (3-hour)
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Process forecast data
                daily_forecasts = self._process_forecast_data(data, days)
                
                return ForecastResponse(
                    location=f"{data['city']['name']}, {data['city']['country']}",
                    forecast=daily_forecasts
                )
                
        except Exception as e:
            logger.error(f"Error fetching forecast: {str(e)}")
            return self._get_mock_forecast(location, days)
    
    def _process_forecast_data(self, data: Dict, days: int) -> List[ForecastDay]:
        """Process raw forecast data into daily summaries"""
        daily_data = {}
        
        for item in data.get('list', []):
            date = item['dt_txt'].split(' ')[0]
            
            if date not in daily_data:
                daily_data[date] = {
                    'temps': [],
                    'conditions': [],
                    'descriptions': [],
                    'icons': []
                }
            
            daily_data[date]['temps'].append(item['main']['temp'])
            daily_data[date]['conditions'].append(item['weather'][0]['main'])
            daily_data[date]['descriptions'].append(item['weather'][0]['description'])
            daily_data[date]['icons'].append(item['weather'][0]['icon'])
        
        forecasts = []
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for date, day_data in list(daily_data.items())[:days]:
            dt = datetime.strptime(date, '%Y-%m-%d')
            
            forecasts.append(ForecastDay(
                date=date,
                day_of_week=day_names[dt.weekday()],
                high_temp=max(day_data['temps']),
                low_temp=min(day_data['temps']),
                condition=max(set(day_data['conditions']), key=day_data['conditions'].count),
                description=max(set(day_data['descriptions']), key=day_data['descriptions'].count),
                icon=day_data['icons'][len(day_data['icons'])//2]  # Midday icon
            ))
        
        return forecasts
    
    def _get_mock_forecast(self, location: str, days: int) -> ForecastResponse:
        """Return mock forecast for development/testing"""
        from datetime import timedelta
        
        forecasts = []
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        conditions = ['Clear', 'Clouds', 'Clear', 'Rain', 'Clear']
        
        for i in range(min(days, 5)):
            dt = datetime.now() + timedelta(days=i)
            forecasts.append(ForecastDay(
                date=dt.strftime('%Y-%m-%d'),
                day_of_week=day_names[dt.weekday()],
                high_temp=22 + i,
                low_temp=15 + i,
                condition=conditions[i],
                description=conditions[i].lower()
            ))
        
        return ForecastResponse(
            location=location,
            forecast=forecasts
        )
    
    async def search_location(self, query: str, limit: int = 5) -> List[LocationSearchResult]:
        """
        Search for locations by name
        
        Args:
            query: Location search query
            limit: Maximum results to return
            
        Returns:
            List of matching locations
        """
        if not self.api_key:
            return [LocationSearchResult(
                name=query,
                country="Unknown",
                lat=0.0,
                lon=0.0
            )]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.GEO_URL}/direct",
                    params={
                        "q": query,
                        "limit": limit,
                        "appid": self.api_key
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                return [
                    LocationSearchResult(
                        name=loc['name'],
                        country=loc.get('country', ''),
                        state=loc.get('state'),
                        lat=loc['lat'],
                        lon=loc['lon']
                    )
                    for loc in data
                ]
                
        except Exception as e:
            logger.error(f"Error searching location: {str(e)}")
            return []


# Singleton instance
_service_instance: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    """Get or create the Weather service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = WeatherService()
    return _service_instance
