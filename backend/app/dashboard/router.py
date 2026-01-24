"""
Dashboard Router - API endpoints for the main dashboard
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional
from datetime import date
import logging

from .schemas import (
    DashboardData,
    DashboardRequest,
    OutfitCard,
    OutfitCarousel,
    OutfitOfTheDayRequest
)
from .service import DashboardService, get_dashboard_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
    responses={
        500: {"description": "Internal server error"}
    }
)


@router.get(
    "",
    response_model=DashboardData,
    summary="Get Dashboard",
    description="Get complete dashboard data for a user"
)
async def get_dashboard(
    user_id: str = Query(..., description="User ID"),
    location: Optional[str] = Query(default=None, description="Location for weather"),
    include_weather: bool = Query(default=True),
    include_events: bool = Query(default=True),
    include_outfits: bool = Query(default=True),
    outfit_count: int = Query(default=5, ge=1, le=20),
    event_hours_ahead: int = Query(default=24, ge=1, le=168),
    service: DashboardService = Depends(get_dashboard_service)
) -> DashboardData:
    """
    Get the complete dashboard data for a user.
    
    The dashboard combines:
    - Weather widget with outfit advice
    - Upcoming calendar events
    - Outfit recommendations carousel
    - User stats and quick actions
    
    Parameters:
    - **user_id**: User ID (required)
    - **location**: City for weather data
    - **include_weather**: Include weather widget
    - **include_events**: Include calendar events
    - **include_outfits**: Include outfit recommendations
    - **outfit_count**: Number of outfits in carousel (1-20)
    - **event_hours_ahead**: Hours ahead for events (1-168)
    """
    try:
        return await service.get_dashboard(
            user_id=user_id,
            location=location,
            include_weather=include_weather,
            include_events=include_events,
            include_outfits=include_outfits,
            outfit_count=outfit_count,
            event_hours_ahead=event_hours_ahead
        )
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard: {str(e)}"
        )


@router.post(
    "",
    response_model=DashboardData,
    summary="Get Dashboard (POST)",
    description="Get dashboard data with detailed request options"
)
async def get_dashboard_post(
    request: DashboardRequest,
    service: DashboardService = Depends(get_dashboard_service)
) -> DashboardData:
    """
    Get dashboard data with full request options.
    
    Same as GET but allows more complex request body.
    """
    try:
        return await service.get_dashboard(
            user_id=request.user_id,
            location=request.location,
            include_weather=request.include_weather,
            include_events=request.include_events,
            include_outfits=request.include_outfits,
            outfit_count=request.outfit_count,
            event_hours_ahead=request.event_hours_ahead
        )
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard: {str(e)}"
        )


@router.get(
    "/outfit-of-the-day",
    response_model=OutfitCard,
    summary="Get Outfit of the Day",
    description="Get the AI-curated outfit of the day"
)
async def get_outfit_of_the_day(
    user_id: str = Query(..., description="User ID"),
    location: Optional[str] = Query(default=None, description="Location for weather"),
    occasion: Optional[str] = Query(default=None, description="Specific occasion"),
    target_date: Optional[date] = Query(default=None, description="Target date"),
    service: DashboardService = Depends(get_dashboard_service)
) -> OutfitCard:
    """
    Get the outfit of the day recommendation.
    
    The AI considers:
    - User's style profile
    - Current weather conditions
    - Upcoming calendar events
    - Time of day
    
    Parameters:
    - **user_id**: User ID (required)
    - **location**: City for weather-appropriate suggestions
    - **occasion**: Specific occasion to dress for
    - **target_date**: Date for the outfit (defaults to today)
    """
    try:
        return await service.get_outfit_of_the_day(
            user_id=user_id,
            location=location,
            occasion=occasion,
            target_date=target_date
        )
    except Exception as e:
        logger.error(f"Outfit of the day error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get outfit: {str(e)}"
        )


@router.get(
    "/outfits",
    response_model=OutfitCarousel,
    summary="Get Outfit Carousel",
    description="Get outfit recommendations carousel"
)
async def get_outfit_carousel(
    user_id: str = Query(..., description="User ID"),
    count: int = Query(default=5, ge=1, le=20),
    page: int = Query(default=1, ge=1),
    occasion: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
    service: DashboardService = Depends(get_dashboard_service)
) -> OutfitCarousel:
    """
    Get outfit recommendations carousel.
    
    Parameters:
    - **user_id**: User ID (required)
    - **count**: Number of outfits per page
    - **page**: Page number
    - **occasion**: Filter by occasion
    - **location**: Location for weather-appropriate filtering
    """
    try:
        weather = None
        if location:
            weather = await service._get_weather_widget(location)
        
        events = await service._get_upcoming_events(user_id, hours_ahead=24)
        
        carousel = await service._get_outfit_carousel(
            user_id=user_id,
            count=count,
            weather=weather,
            events=events
        )
        
        carousel.page = page
        return carousel
        
    except Exception as e:
        logger.error(f"Outfit carousel error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get outfits: {str(e)}"
        )


@router.get(
    "/quick-actions",
    summary="Get Quick Actions",
    description="Get available quick actions for the dashboard"
)
async def get_quick_actions(
    user_id: str = Query(..., description="User ID"),
    service: DashboardService = Depends(get_dashboard_service)
) -> dict:
    """
    Get quick action buttons for the dashboard.
    
    Returns customized quick actions based on user preferences.
    """
    return {
        "user_id": user_id,
        "actions": [action.model_dump() for action in service.DEFAULT_QUICK_ACTIONS]
    }


@router.get(
    "/style-tip",
    summary="Get Style Tip",
    description="Get a random style tip"
)
async def get_style_tip(
    service: DashboardService = Depends(get_dashboard_service)
) -> dict:
    """Get a random style tip for the user."""
    return {
        "tip": service._get_random_tip()
    }


@router.get(
    "/greeting",
    summary="Get Greeting",
    description="Get time-appropriate greeting"
)
async def get_greeting(
    user_name: Optional[str] = Query(default=None, description="User's name"),
    service: DashboardService = Depends(get_dashboard_service)
) -> dict:
    """Get a personalized, time-appropriate greeting."""
    greeting = service._get_greeting()
    
    if user_name:
        # Remove emoji from end to insert name
        base_greeting = greeting.rstrip("☀️👋🌆🌙 ")
        greeting = f"{base_greeting}, {user_name}!"
    
    return {"greeting": greeting}


@router.get(
    "/health",
    summary="Health Check",
    description="Check dashboard service health"
)
async def health_check(
    service: DashboardService = Depends(get_dashboard_service)
) -> dict:
    """Check the health of the dashboard service."""
    return {
        "status": "healthy",
        "weather_service": service._weather_service is not None,
        "calendar_service": service._calendar_service is not None,
        "recommendation_service": service._recommendation_service is not None
    }
