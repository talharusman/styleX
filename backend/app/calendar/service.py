"""
Calendar Service - Handles Google Calendar API interactions
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import httpx

from .schemas import (
    CalendarEvent,
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarMonthView,
    CalendarDayView,
    EventStatus,
    EventAttendee,
    Reminder
)
from .oauth import GoogleOAuth, get_google_oauth

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for interacting with Google Calendar API"""
    
    CALENDAR_API_URL = "https://www.googleapis.com/calendar/v3"
    
    def __init__(self, oauth: Optional[GoogleOAuth] = None):
        """
        Initialize Calendar service
        
        Args:
            oauth: GoogleOAuth instance for authentication
        """
        self.oauth = oauth or get_google_oauth()
        
        # In-memory token storage (use DB in production)
        self._user_tokens: Dict[str, Dict[str, Any]] = {}
    
    def set_user_tokens(self, user_id: str, tokens: Dict[str, Any]):
        """Store tokens for a user"""
        self._user_tokens[user_id] = {
            **tokens,
            "stored_at": datetime.utcnow()
        }
    
    def get_user_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get stored tokens for a user"""
        return self._user_tokens.get(user_id)
    
    async def _get_valid_token(self, user_id: str) -> str:
        """Get a valid access token, refreshing if necessary"""
        tokens = self.get_user_tokens(user_id)
        
        if not tokens:
            raise ValueError("User not authenticated with Google Calendar")
        
        # Check if token is expired (with 5 minute buffer)
        stored_at = tokens.get("stored_at", datetime.utcnow())
        expires_in = tokens.get("expires_in", 3600)
        
        if datetime.utcnow() - stored_at > timedelta(seconds=expires_in - 300):
            # Token is expired or about to expire
            if tokens.get("refresh_token"):
                new_tokens = await self.oauth.refresh_access_token(tokens["refresh_token"])
                self.set_user_tokens(user_id, {
                    **new_tokens,
                    "refresh_token": tokens["refresh_token"]  # Keep refresh token
                })
                return new_tokens["access_token"]
            else:
                raise ValueError("Token expired and no refresh token available")
        
        return tokens["access_token"]
    
    async def list_events(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        calendar_id: str = "primary",
        max_results: int = 50,
        include_cancelled: bool = False
    ) -> List[CalendarEvent]:
        """
        List calendar events for a date range
        
        Args:
            user_id: User ID
            start_date: Start of date range
            end_date: End of date range
            calendar_id: Calendar ID (default: primary)
            max_results: Maximum number of events
            include_cancelled: Include cancelled events
            
        Returns:
            List of calendar events
        """
        access_token = await self._get_valid_token(user_id)
        
        # Default to current month if no dates specified
        if not start_date:
            now = datetime.now()
            start_date = date(now.year, now.month, 1)
        if not end_date:
            # Last day of the month
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_date = next_month.replace(day=1) - timedelta(days=1)
        
        # Convert to RFC3339 format
        time_min = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
        time_max = datetime.combine(end_date, datetime.max.time()).isoformat() + "Z"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.CALENDAR_API_URL}/calendars/{calendar_id}/events",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params={
                        "timeMin": time_min,
                        "timeMax": time_max,
                        "maxResults": max_results,
                        "singleEvents": True,
                        "orderBy": "startTime",
                        "showDeleted": include_cancelled
                    }
                )
                
                if response.status_code == 401:
                    raise ValueError("Authentication expired")
                
                response.raise_for_status()
                data = response.json()
                
                return [self._parse_event(event) for event in data.get("items", [])]
                
        except httpx.HTTPError as e:
            logger.error(f"Error fetching events: {str(e)}")
            raise
    
    async def get_event(
        self,
        user_id: str,
        event_id: str,
        calendar_id: str = "primary"
    ) -> CalendarEvent:
        """Get a single calendar event by ID"""
        access_token = await self._get_valid_token(user_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.CALENDAR_API_URL}/calendars/{calendar_id}/events/{event_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            response.raise_for_status()
            return self._parse_event(response.json())
    
    async def create_event(
        self,
        user_id: str,
        event_data: CalendarEventCreate,
        calendar_id: str = "primary"
    ) -> CalendarEvent:
        """
        Create a new calendar event
        
        Args:
            user_id: User ID
            event_data: Event creation data
            calendar_id: Calendar ID
            
        Returns:
            Created calendar event
        """
        access_token = await self._get_valid_token(user_id)
        
        # Build event body
        body = {
            "summary": event_data.summary,
            "description": event_data.description,
            "location": event_data.location,
            "visibility": event_data.visibility.value
        }
        
        # Handle all-day vs timed events
        if event_data.all_day:
            body["start"] = {"date": event_data.start.date().isoformat()}
            body["end"] = {"date": event_data.end.date().isoformat()}
        else:
            body["start"] = {
                "dateTime": event_data.start.isoformat(),
                "timeZone": event_data.timezone
            }
            body["end"] = {
                "dateTime": event_data.end.isoformat(),
                "timeZone": event_data.timezone
            }
        
        # Add attendees
        if event_data.attendees:
            body["attendees"] = [
                {"email": a.email, "displayName": a.display_name, "optional": a.optional}
                for a in event_data.attendees
            ]
        
        # Add reminders
        if event_data.reminders:
            body["reminders"] = {
                "useDefault": False,
                "overrides": [
                    {"method": r.method.value, "minutes": r.minutes}
                    for r in event_data.reminders
                ]
            }
        
        # Add color
        if event_data.color_id:
            body["colorId"] = event_data.color_id
        
        # Add StyleX metadata in extended properties
        body["extendedProperties"] = {
            "private": {
                "stylex_outfit_enabled": str(event_data.outfit_suggestion_enabled).lower(),
                "stylex_event_type": event_data.event_type or ""
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.CALENDAR_API_URL}/calendars/{calendar_id}/events",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=body
            )
            
            response.raise_for_status()
            return self._parse_event(response.json())
    
    async def update_event(
        self,
        user_id: str,
        event_id: str,
        event_data: CalendarEventUpdate,
        calendar_id: str = "primary"
    ) -> CalendarEvent:
        """Update an existing calendar event"""
        access_token = await self._get_valid_token(user_id)
        
        # Get current event
        current_event = await self.get_event(user_id, event_id, calendar_id)
        
        # Build update body with only changed fields
        body = {}
        
        if event_data.summary is not None:
            body["summary"] = event_data.summary
        if event_data.description is not None:
            body["description"] = event_data.description
        if event_data.location is not None:
            body["location"] = event_data.location
        if event_data.visibility is not None:
            body["visibility"] = event_data.visibility.value
        if event_data.status is not None:
            body["status"] = event_data.status.value
        if event_data.color_id is not None:
            body["colorId"] = event_data.color_id
        
        # Handle time changes
        if event_data.start is not None or event_data.end is not None:
            all_day = event_data.all_day if event_data.all_day is not None else current_event.all_day
            timezone = event_data.timezone or current_event.timezone
            
            if all_day:
                if event_data.start:
                    body["start"] = {"date": event_data.start.date().isoformat()}
                if event_data.end:
                    body["end"] = {"date": event_data.end.date().isoformat()}
            else:
                if event_data.start:
                    body["start"] = {
                        "dateTime": event_data.start.isoformat(),
                        "timeZone": timezone
                    }
                if event_data.end:
                    body["end"] = {
                        "dateTime": event_data.end.isoformat(),
                        "timeZone": timezone
                    }
        
        # Handle attendees
        if event_data.attendees is not None:
            body["attendees"] = [
                {"email": a.email, "displayName": a.display_name, "optional": a.optional}
                for a in event_data.attendees
            ]
        
        # Handle reminders
        if event_data.reminders is not None:
            body["reminders"] = {
                "useDefault": False,
                "overrides": [
                    {"method": r.method.value, "minutes": r.minutes}
                    for r in event_data.reminders
                ]
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.CALENDAR_API_URL}/calendars/{calendar_id}/events/{event_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=body
            )
            
            response.raise_for_status()
            return self._parse_event(response.json())
    
    async def delete_event(
        self,
        user_id: str,
        event_id: str,
        calendar_id: str = "primary"
    ) -> bool:
        """Delete a calendar event"""
        access_token = await self._get_valid_token(user_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.CALENDAR_API_URL}/calendars/{calendar_id}/events/{event_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            return response.status_code == 204
    
    async def get_month_view(
        self,
        user_id: str,
        year: int,
        month: int,
        calendar_id: str = "primary"
    ) -> CalendarMonthView:
        """
        Get calendar events for a specific month
        
        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)
            calendar_id: Calendar ID
            
        Returns:
            Month view with all events
        """
        start_date = date(year, month, 1)
        
        # Calculate last day of month
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        events = await self.list_events(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            calendar_id=calendar_id,
            max_results=250
        )
        
        return CalendarMonthView(
            year=year,
            month=month,
            events=events,
            total_events=len(events),
            has_more=len(events) >= 250
        )
    
    async def get_day_view(
        self,
        user_id: str,
        day: date,
        calendar_id: str = "primary",
        include_weather: bool = True,
        include_outfit: bool = True
    ) -> CalendarDayView:
        """
        Get calendar events for a specific day with weather and outfit suggestions
        
        Args:
            user_id: User ID
            day: The date to get events for
            calendar_id: Calendar ID
            include_weather: Include weather data
            include_outfit: Include outfit suggestion
            
        Returns:
            Day view with events, weather, and outfit suggestion
        """
        events = await self.list_events(
            user_id=user_id,
            start_date=day,
            end_date=day,
            calendar_id=calendar_id
        )
        
        day_view = CalendarDayView(
            date=day,
            events=events
        )
        
        # Weather and outfit can be added by integrating with other services
        # This would be done at the router level to inject dependencies
        
        return day_view
    
    async def get_upcoming_events(
        self,
        user_id: str,
        hours: int = 24,
        calendar_id: str = "primary"
    ) -> List[CalendarEvent]:
        """Get events in the next N hours"""
        now = datetime.now()
        end_time = now + timedelta(hours=hours)
        
        return await self.list_events(
            user_id=user_id,
            start_date=now.date(),
            end_date=end_time.date(),
            calendar_id=calendar_id
        )
    
    def _parse_event(self, event_data: Dict[str, Any]) -> CalendarEvent:
        """Parse Google Calendar event data into CalendarEvent model"""
        
        # Handle start time
        start_data = event_data.get("start", {})
        if "dateTime" in start_data:
            start = datetime.fromisoformat(start_data["dateTime"].replace("Z", "+00:00"))
            all_day = False
        else:
            start = datetime.combine(
                date.fromisoformat(start_data.get("date", "")),
                datetime.min.time()
            )
            all_day = True
        
        # Handle end time
        end_data = event_data.get("end", {})
        if "dateTime" in end_data:
            end = datetime.fromisoformat(end_data["dateTime"].replace("Z", "+00:00"))
        else:
            end = datetime.combine(
                date.fromisoformat(end_data.get("date", "")),
                datetime.max.time()
            )
        
        # Parse attendees
        attendees = [
            EventAttendee(
                email=a["email"],
                display_name=a.get("displayName"),
                response_status=a.get("responseStatus", "needsAction"),
                optional=a.get("optional", False)
            )
            for a in event_data.get("attendees", [])
        ]
        
        # Parse reminders
        reminders = []
        reminder_data = event_data.get("reminders", {})
        if not reminder_data.get("useDefault", True):
            for r in reminder_data.get("overrides", []):
                reminders.append(Reminder(
                    method=r.get("method", "popup"),
                    minutes=r.get("minutes", 30)
                ))
        
        # Get StyleX metadata
        extended = event_data.get("extendedProperties", {}).get("private", {})
        event_type = extended.get("stylex_event_type")
        outfit_suggestion = extended.get("stylex_outfit_suggestion")
        
        return CalendarEvent(
            id=event_data["id"],
            summary=event_data.get("summary", "(No title)"),
            description=event_data.get("description"),
            location=event_data.get("location"),
            start=start,
            end=end,
            all_day=all_day,
            timezone=start_data.get("timeZone", "UTC"),
            status=EventStatus(event_data.get("status", "confirmed")),
            html_link=event_data.get("htmlLink"),
            hangout_link=event_data.get("hangoutLink"),
            attendees=attendees,
            reminders=reminders,
            color_id=event_data.get("colorId"),
            creator_email=event_data.get("creator", {}).get("email"),
            organizer_email=event_data.get("organizer", {}).get("email"),
            created=datetime.fromisoformat(event_data["created"].replace("Z", "+00:00")) if "created" in event_data else None,
            updated=datetime.fromisoformat(event_data["updated"].replace("Z", "+00:00")) if "updated" in event_data else None,
            event_type=event_type,
            outfit_suggestion=outfit_suggestion
        )


# Singleton instance
_service_instance: Optional[CalendarService] = None


def get_calendar_service() -> CalendarService:
    """Get or create the Calendar service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = CalendarService()
    return _service_instance
