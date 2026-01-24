"""
Dashboard Service - Aggregates data for the main dashboard view
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import uuid

from .schemas import (
    DashboardData,
    WeatherWidget,
    EventWidget,
    OutfitCard,
    OutfitCarousel,
    UserStats,
    QuickAction
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for aggregating dashboard data"""
    
    DEFAULT_QUICK_ACTIONS = [
        QuickAction(
            id="new_outfit",
            label="New Outfit",
            icon="plus",
            action_type="navigate",
            destination="/recommendation/new"
        ),
        QuickAction(
            id="add_event",
            label="Add Event",
            icon="calendar-plus",
            action_type="navigate",
            destination="/calendar/new"
        ),
        QuickAction(
            id="chat",
            label="Ask Stylist",
            icon="message",
            action_type="navigate",
            destination="/chat"
        ),
        QuickAction(
            id="wardrobe",
            label="Wardrobe",
            icon="hanger",
            action_type="navigate",
            destination="/wardrobe"
        )
    ]
    
    STYLE_TIPS = [
        "Mixing textures adds depth to any outfit - try pairing a chunky knit with smooth leather.",
        "When in doubt, stick to the rule of three colors maximum in an outfit.",
        "Rolling your sleeves can instantly make an outfit look more relaxed and intentional.",
        "Accessories can transform a basic outfit into something special.",
        "Invest in quality basics - they're the foundation of a versatile wardrobe.",
        "Match your metals: if your watch is silver, consider silver jewelry too.",
        "Tucking in your shirt can make you look taller and more put-together.",
        "Don't forget about proportions - balance oversized tops with fitted bottoms or vice versa."
    ]
    
    def __init__(self):
        """Initialize dashboard service"""
        # These would be injected in a real app
        self._weather_service = None
        self._calendar_service = None
        self._recommendation_service = None
    
    def set_services(
        self,
        weather_service=None,
        calendar_service=None,
        recommendation_service=None
    ):
        """Set dependent services"""
        self._weather_service = weather_service
        self._calendar_service = calendar_service
        self._recommendation_service = recommendation_service
    
    async def get_dashboard(
        self,
        user_id: str,
        location: Optional[str] = None,
        include_weather: bool = True,
        include_events: bool = True,
        include_outfits: bool = True,
        outfit_count: int = 5,
        event_hours_ahead: int = 24
    ) -> DashboardData:
        """
        Get complete dashboard data for a user.
        
        Args:
            user_id: User ID
            location: Location for weather
            include_weather: Include weather widget
            include_events: Include calendar events
            include_outfits: Include outfit recommendations
            outfit_count: Number of outfits to include
            event_hours_ahead: Hours ahead for events
            
        Returns:
            Complete dashboard data
        """
        dashboard = DashboardData(
            user_id=user_id,
            greeting=self._get_greeting(),
            quick_actions=self.DEFAULT_QUICK_ACTIONS,
            style_tip=self._get_random_tip()
        )
        
        # Get weather
        if include_weather and location:
            dashboard.weather = await self._get_weather_widget(location)
        
        # Get upcoming events
        if include_events:
            dashboard.upcoming_events = await self._get_upcoming_events(
                user_id=user_id,
                hours_ahead=event_hours_ahead
            )
        
        # Get outfit recommendations
        if include_outfits:
            dashboard.outfit_carousel = await self._get_outfit_carousel(
                user_id=user_id,
                count=outfit_count,
                weather=dashboard.weather,
                events=dashboard.upcoming_events
            )
            
            # Set outfit of the day
            if dashboard.outfit_carousel.outfits:
                dashboard.outfit_of_the_day = dashboard.outfit_carousel.outfits[0]
        
        # Get user stats
        dashboard.stats = await self._get_user_stats(user_id)
        
        # Set cache expiration
        dashboard.cache_expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        return dashboard
    
    def _get_greeting(self) -> str:
        """Get time-appropriate greeting"""
        hour = datetime.now().hour
        
        if hour < 12:
            return "Good morning! ☀️"
        elif hour < 17:
            return "Good afternoon! 👋"
        elif hour < 21:
            return "Good evening! 🌆"
        else:
            return "Good night! 🌙"
    
    def _get_random_tip(self) -> str:
        """Get a random style tip"""
        import random
        return random.choice(self.STYLE_TIPS)
    
    async def _get_weather_widget(self, location: str) -> Optional[WeatherWidget]:
        """Get weather widget data"""
        try:
            if self._weather_service:
                weather_response = await self._weather_service.get_weather(location)
                return WeatherWidget(
                    location=weather_response.weather.location,
                    temperature=weather_response.weather.temperature,
                    condition=weather_response.weather.condition,
                    description=weather_response.weather.description,
                    humidity=weather_response.weather.humidity,
                    icon=weather_response.weather.icon,
                    outfit_advice=weather_response.weather_advice,
                    recommended_colors=weather_response.recommended_colors
                )
            
            # Return mock data if service not available
            return WeatherWidget(
                location=location,
                temperature=22.0,
                condition="Clear",
                description="clear sky",
                humidity=45,
                outfit_advice="Perfect weather for light layers!",
                recommended_colors=["light blue", "beige", "white"]
            )
            
        except Exception as e:
            logger.error(f"Error getting weather: {str(e)}")
            return None
    
    async def _get_upcoming_events(
        self,
        user_id: str,
        hours_ahead: int
    ) -> List[EventWidget]:
        """Get upcoming calendar events"""
        try:
            if self._calendar_service:
                events = await self._calendar_service.get_upcoming_events(
                    user_id=user_id,
                    hours=hours_ahead
                )
                
                return [
                    EventWidget(
                        id=event.id,
                        title=event.summary,
                        start_time=event.start,
                        end_time=event.end,
                        location=event.location,
                        is_today=event.start.date() == date.today(),
                        time_until=self._format_time_until(event.start)
                    )
                    for event in events[:5]  # Limit to 5 events
                ]
            
            # Return mock data if service not available
            return [
                EventWidget(
                    id="mock-1",
                    title="Team Meeting",
                    start_time=datetime.now() + timedelta(hours=2),
                    end_time=datetime.now() + timedelta(hours=3),
                    location="Conference Room A",
                    is_today=True,
                    time_until="in 2 hours"
                )
            ]
            
        except Exception as e:
            logger.warning(f"Error getting events: {str(e)}")
            return []
    
    def _format_time_until(self, event_time: datetime) -> str:
        """Format time until event in human-readable form"""
        now = datetime.now()
        
        if event_time.tzinfo:
            now = now.replace(tzinfo=event_time.tzinfo)
        
        diff = event_time - now
        
        if diff.total_seconds() < 0:
            return "now"
        
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        
        if hours > 24:
            days = hours // 24
            return f"in {days} day{'s' if days > 1 else ''}"
        elif hours > 0:
            return f"in {hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"in {minutes} minute{'s' if minutes > 1 else ''}"
    
    async def _get_outfit_carousel(
        self,
        user_id: str,
        count: int,
        weather: Optional[WeatherWidget],
        events: List[EventWidget]
    ) -> OutfitCarousel:
        """Get outfit recommendations carousel"""
        try:
            # This would integrate with the recommendation service
            # For now, return mock data
            outfits = self._generate_mock_outfits(
                count=count,
                weather=weather,
                events=events
            )
            
            return OutfitCarousel(
                outfits=outfits,
                total_count=len(outfits),
                page=1,
                page_size=count
            )
            
        except Exception as e:
            logger.error(f"Error getting outfits: {str(e)}")
            return OutfitCarousel()
    
    def _generate_mock_outfits(
        self,
        count: int,
        weather: Optional[WeatherWidget],
        events: List[EventWidget]
    ) -> List[OutfitCard]:
        """Generate mock outfit recommendations"""
        occasions = ["casual", "work", "evening", "weekend", "date night"]
        
        outfits = []
        for i in range(count):
            occasion = occasions[i % len(occasions)]
            
            outfit = OutfitCard(
                id=str(uuid.uuid4()),
                title=f"{occasion.title()} Look",
                description=f"Perfect for your {occasion} activities",
                occasion=occasion,
                items=self._get_items_for_occasion(occasion, weather),
                colors=["navy", "white", "beige"],
                style_tags=[occasion, "comfortable", "stylish"],
                confidence_score=0.85 - (i * 0.05),
                is_weather_appropriate=True,
                is_event_appropriate=True
            )
            outfits.append(outfit)
        
        return outfits
    
    def _get_items_for_occasion(
        self,
        occasion: str,
        weather: Optional[WeatherWidget]
    ) -> List[str]:
        """Get clothing items for an occasion"""
        items_map = {
            "casual": ["slim jeans", "cotton t-shirt", "sneakers", "light jacket"],
            "work": ["dress pants", "button-down shirt", "blazer", "oxford shoes"],
            "evening": ["dark jeans", "fitted shirt", "leather jacket", "boots"],
            "weekend": ["chinos", "polo shirt", "loafers", "sunglasses"],
            "date night": ["tailored pants", "elegant top", "heels/dress shoes", "statement accessory"]
        }
        
        return items_map.get(occasion, items_map["casual"])
    
    async def _get_user_stats(self, user_id: str) -> UserStats:
        """Get user statistics"""
        # This would fetch from database in production
        return UserStats(
            total_outfits_viewed=42,
            favorites_count=12,
            wardrobe_items=67,
            events_this_week=5,
            style_score=8.5
        )
    
    async def get_outfit_of_the_day(
        self,
        user_id: str,
        location: Optional[str] = None,
        occasion: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> OutfitCard:
        """
        Get the outfit of the day recommendation.
        
        Combines user profile, weather, and calendar events
        to suggest the best outfit.
        """
        # Get weather if location provided
        weather = None
        if location:
            weather = await self._get_weather_widget(location)
        
        # Get events for the day
        events = await self._get_upcoming_events(user_id, hours_ahead=12)
        
        # Determine occasion from events or use provided
        if not occasion and events:
            occasion = self._infer_occasion_from_events(events)
        
        occasion = occasion or "casual"
        
        return OutfitCard(
            id=str(uuid.uuid4()),
            title="Outfit of the Day",
            description=f"Curated for your {occasion} day" + 
                       (f" in {weather.temperature}° weather" if weather else ""),
            occasion=occasion,
            items=self._get_items_for_occasion(occasion, weather),
            colors=weather.recommended_colors if weather else ["navy", "grey", "white"],
            style_tags=[occasion, "recommended", "ai-picked"],
            confidence_score=0.92,
            is_weather_appropriate=True,
            is_event_appropriate=True
        )
    
    def _infer_occasion_from_events(self, events: List[EventWidget]) -> str:
        """Infer dress occasion from calendar events"""
        for event in events:
            title_lower = event.title.lower()
            
            if any(word in title_lower for word in ["meeting", "presentation", "interview"]):
                return "work"
            elif any(word in title_lower for word in ["dinner", "party", "celebration"]):
                return "evening"
            elif any(word in title_lower for word in ["date", "romantic"]):
                return "date night"
            elif any(word in title_lower for word in ["gym", "workout", "sports"]):
                return "sporty"
        
        return "casual"


# Singleton instance
_service_instance: Optional[DashboardService] = None


def get_dashboard_service() -> DashboardService:
    """Get or create the Dashboard service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = DashboardService()
    return _service_instance
