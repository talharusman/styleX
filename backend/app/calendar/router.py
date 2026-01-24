"""
Calendar Router - API endpoints for Google Calendar integration
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
from fastapi.responses import RedirectResponse
from typing import Optional
from datetime import date, datetime
import logging

from .schemas import (
    CalendarEvent,
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarMonthView,
    CalendarDayView,
    EventWithOutfit
)
from .service import CalendarService, get_calendar_service
from .oauth import GoogleOAuth, get_google_oauth

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/calendar",
    tags=["Calendar"],
    responses={
        401: {"description": "Not authenticated"},
        404: {"description": "Event not found"},
        500: {"description": "Internal server error"}
    }
)


# ============== OAuth Endpoints ==============

@router.get(
    "/auth",
    summary="Start OAuth Flow",
    description="Initiate Google OAuth authentication"
)
async def start_auth(
    user_id: Optional[str] = Query(default=None, description="User ID to link"),
    oauth: GoogleOAuth = Depends(get_google_oauth)
) -> dict:
    """
    Start the Google OAuth authentication flow.
    
    - **user_id**: Optional user ID to associate with the OAuth flow
    
    Returns the authorization URL to redirect the user to.
    """
    if not oauth.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )
    
    auth_data = oauth.generate_auth_url(user_id=user_id)
    
    return {
        "auth_url": auth_data["auth_url"],
        "state": auth_data["state"],
        "message": "Redirect user to auth_url to complete authentication"
    }


@router.get(
    "/auth/callback",
    summary="OAuth Callback",
    description="Handle OAuth callback from Google"
)
async def auth_callback(
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State token"),
    error: Optional[str] = Query(default=None),
    oauth: GoogleOAuth = Depends(get_google_oauth),
    service: CalendarService = Depends(get_calendar_service)
):
    """
    Handle the OAuth callback from Google.
    
    This endpoint is called by Google after user authentication.
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {error}"
        )
    
    try:
        # Exchange code for tokens
        token_data = await oauth.exchange_code(code, state)
        
        # Store tokens for the user
        user_id = token_data.get("stored_user_id") or token_data["user_info"]["id"]
        service.set_user_tokens(user_id, token_data)
        
        return {
            "success": True,
            "user_id": user_id,
            "email": token_data["user_info"].get("email"),
            "name": token_data["user_info"].get("name"),
            "message": "Successfully authenticated with Google Calendar"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete authentication"
        )


@router.post(
    "/auth/revoke",
    summary="Revoke OAuth Access",
    description="Revoke Google Calendar access"
)
async def revoke_access(
    user_id: str = Query(..., description="User ID"),
    oauth: GoogleOAuth = Depends(get_google_oauth),
    service: CalendarService = Depends(get_calendar_service)
) -> dict:
    """
    Revoke the user's Google Calendar access.
    
    - **user_id**: User ID whose access to revoke
    """
    tokens = service.get_user_tokens(user_id)
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not authenticated"
        )
    
    # Revoke the token
    access_token = tokens.get("access_token")
    if access_token:
        await oauth.revoke_token(access_token)
    
    # Clear stored tokens
    service._user_tokens.pop(user_id, None)
    
    return {"success": True, "message": "Access revoked successfully"}


# ============== Calendar Event Endpoints ==============

@router.get(
    "",
    response_model=list[CalendarEvent],
    summary="List Events",
    description="Get calendar events for a date range"
)
async def list_events(
    user_id: str = Query(..., description="User ID"),
    start_date: Optional[date] = Query(default=None, description="Start date"),
    end_date: Optional[date] = Query(default=None, description="End date"),
    max_results: int = Query(default=50, ge=1, le=250),
    service: CalendarService = Depends(get_calendar_service)
) -> list[CalendarEvent]:
    """
    List calendar events for a date range.
    
    - **user_id**: User ID (must be authenticated)
    - **start_date**: Start of date range (defaults to today)
    - **end_date**: End of date range (defaults to end of month)
    - **max_results**: Maximum events to return
    
    Returns list of calendar events.
    """
    try:
        events = await service.list_events(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results
        )
        return events
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"List events error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch events: {str(e)}"
        )


@router.get(
    "/month/{year}/{month}",
    response_model=CalendarMonthView,
    summary="Get Month View",
    description="Get all events for a specific month"
)
async def get_month_view(
    year: int,
    month: int,
    user_id: str = Query(..., description="User ID"),
    service: CalendarService = Depends(get_calendar_service)
) -> CalendarMonthView:
    """
    Get calendar month view with all events.
    
    - **year**: Year (e.g., 2024)
    - **month**: Month (1-12)
    - **user_id**: User ID
    
    Returns month view with all events.
    """
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    try:
        return await service.get_month_view(user_id=user_id, year=year, month=month)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get(
    "/day/{year}/{month}/{day}",
    response_model=CalendarDayView,
    summary="Get Day View",
    description="Get events for a specific day with weather and outfit suggestions"
)
async def get_day_view(
    year: int,
    month: int,
    day: int,
    user_id: str = Query(..., description="User ID"),
    include_weather: bool = Query(default=True),
    include_outfit: bool = Query(default=True),
    service: CalendarService = Depends(get_calendar_service)
) -> CalendarDayView:
    """
    Get calendar day view with events, weather, and outfit suggestions.
    
    - **year**: Year
    - **month**: Month (1-12)
    - **day**: Day
    - **user_id**: User ID
    - **include_weather**: Include weather data
    - **include_outfit**: Include outfit suggestion
    """
    try:
        target_date = date(year, month, day)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date"
        )
    
    try:
        return await service.get_day_view(
            user_id=user_id,
            day=target_date,
            include_weather=include_weather,
            include_outfit=include_outfit
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get(
    "/upcoming",
    response_model=list[CalendarEvent],
    summary="Get Upcoming Events",
    description="Get events in the next N hours"
)
async def get_upcoming_events(
    user_id: str = Query(..., description="User ID"),
    hours: int = Query(default=24, ge=1, le=168, description="Hours ahead"),
    service: CalendarService = Depends(get_calendar_service)
) -> list[CalendarEvent]:
    """
    Get upcoming events.
    
    - **user_id**: User ID
    - **hours**: Number of hours to look ahead (max 168 = 1 week)
    """
    try:
        return await service.get_upcoming_events(user_id=user_id, hours=hours)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get(
    "/{event_id}",
    response_model=CalendarEvent,
    summary="Get Event",
    description="Get a specific calendar event"
)
async def get_event(
    event_id: str,
    user_id: str = Query(..., description="User ID"),
    service: CalendarService = Depends(get_calendar_service)
) -> CalendarEvent:
    """
    Get a specific calendar event by ID.
    
    - **event_id**: Google Calendar event ID
    - **user_id**: User ID
    """
    try:
        return await service.get_event(user_id=user_id, event_id=event_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )


@router.post(
    "",
    response_model=CalendarEvent,
    status_code=status.HTTP_201_CREATED,
    summary="Create Event",
    description="Create a new calendar event"
)
async def create_event(
    event_data: CalendarEventCreate,
    user_id: str = Query(..., description="User ID"),
    service: CalendarService = Depends(get_calendar_service)
) -> CalendarEvent:
    """
    Create a new calendar event.
    
    - **event_data**: Event details
    - **user_id**: User ID
    
    Returns the created event.
    """
    # Validate times
    if event_data.end <= event_data.start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    try:
        return await service.create_event(user_id=user_id, event_data=event_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create event error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}"
        )


@router.patch(
    "/{event_id}",
    response_model=CalendarEvent,
    summary="Update Event",
    description="Update an existing calendar event"
)
async def update_event(
    event_id: str,
    event_data: CalendarEventUpdate,
    user_id: str = Query(..., description="User ID"),
    service: CalendarService = Depends(get_calendar_service)
) -> CalendarEvent:
    """
    Update a calendar event.
    
    - **event_id**: Event ID to update
    - **event_data**: Fields to update
    - **user_id**: User ID
    
    Returns the updated event.
    """
    try:
        return await service.update_event(
            user_id=user_id,
            event_id=event_id,
            event_data=event_data
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update event error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update event: {str(e)}"
        )


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Event",
    description="Delete a calendar event"
)
async def delete_event(
    event_id: str,
    user_id: str = Query(..., description="User ID"),
    service: CalendarService = Depends(get_calendar_service)
):
    """
    Delete a calendar event.
    
    - **event_id**: Event ID to delete
    - **user_id**: User ID
    """
    try:
        success = await service.delete_event(user_id=user_id, event_id=event_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found or already deleted"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# ============== Enhanced Endpoints with AI ==============

@router.get(
    "/{event_id}/outfit",
    response_model=EventWithOutfit,
    summary="Get Event with Outfit Suggestion",
    description="Get event with AI-powered outfit recommendation"
)
async def get_event_with_outfit(
    event_id: str,
    user_id: str = Query(..., description="User ID"),
    location: Optional[str] = Query(default=None, description="Location for weather"),
    service: CalendarService = Depends(get_calendar_service)
) -> EventWithOutfit:
    """
    Get a calendar event with AI-generated outfit suggestion.
    
    - **event_id**: Event ID
    - **user_id**: User ID
    - **location**: Optional location for weather-based suggestions
    
    Returns event with outfit recommendation based on event type and weather.
    """
    try:
        event = await service.get_event(user_id=user_id, event_id=event_id)
        
        # Outfit suggestion would be generated here using GroqChatService
        # This is a placeholder - integrate with groq_chat service
        
        return EventWithOutfit(
            event=event,
            outfit_suggestion="AI outfit suggestion would appear here",
            weather_at_event=None,
            recommended_colors=None
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check if the calendar service is available"
)
async def health_check(
    oauth: GoogleOAuth = Depends(get_google_oauth)
) -> dict:
    """Check the health of the calendar service."""
    return {
        "status": "healthy" if oauth.is_configured() else "limited",
        "oauth_configured": oauth.is_configured(),
        "message": "Full functionality" if oauth.is_configured() else "Configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
    }
