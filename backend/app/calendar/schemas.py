"""
Pydantic schemas for Calendar endpoints
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum


class EventStatus(str, Enum):
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class EventVisibility(str, Enum):
    DEFAULT = "default"
    PUBLIC = "public"
    PRIVATE = "private"


class ReminderMethod(str, Enum):
    EMAIL = "email"
    POPUP = "popup"


class Reminder(BaseModel):
    """Event reminder configuration"""
    method: ReminderMethod = ReminderMethod.POPUP
    minutes: int = Field(default=30, ge=0, le=40320)  # Max 4 weeks


class EventAttendee(BaseModel):
    """Event attendee information"""
    email: EmailStr
    display_name: Optional[str] = None
    response_status: Optional[str] = "needsAction"
    optional: bool = False


class EventTime(BaseModel):
    """Event time with optional timezone"""
    date_time: Optional[datetime] = None
    date: Optional[date] = None  # For all-day events
    timezone: str = Field(default="UTC")


class CalendarEventCreate(BaseModel):
    """Schema for creating a new calendar event"""
    summary: str = Field(..., min_length=1, max_length=255, description="Event title")
    description: Optional[str] = Field(default=None, max_length=8000)
    location: Optional[str] = Field(default=None, max_length=500)
    start: datetime = Field(..., description="Event start time")
    end: datetime = Field(..., description="Event end time")
    all_day: bool = Field(default=False)
    timezone: str = Field(default="UTC")
    attendees: Optional[List[EventAttendee]] = None
    reminders: Optional[List[Reminder]] = Field(
        default_factory=lambda: [Reminder(method=ReminderMethod.POPUP, minutes=30)]
    )
    visibility: EventVisibility = EventVisibility.DEFAULT
    color_id: Optional[str] = None  # Google Calendar color ID
    
    # StyleX-specific fields
    outfit_suggestion_enabled: bool = Field(
        default=True,
        description="Enable AI outfit suggestions for this event"
    )
    event_type: Optional[str] = Field(
        default=None,
        description="Type of event (meeting, casual, formal, etc.)"
    )


class CalendarEventUpdate(BaseModel):
    """Schema for updating an existing calendar event"""
    summary: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=8000)
    location: Optional[str] = Field(default=None, max_length=500)
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    all_day: Optional[bool] = None
    timezone: Optional[str] = None
    attendees: Optional[List[EventAttendee]] = None
    reminders: Optional[List[Reminder]] = None
    visibility: Optional[EventVisibility] = None
    color_id: Optional[str] = None
    status: Optional[EventStatus] = None
    outfit_suggestion_enabled: Optional[bool] = None
    event_type: Optional[str] = None


class CalendarEvent(BaseModel):
    """Full calendar event with all details"""
    id: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
    start: datetime
    end: datetime
    all_day: bool = False
    timezone: str = "UTC"
    status: EventStatus = EventStatus.CONFIRMED
    html_link: Optional[str] = None
    hangout_link: Optional[str] = None
    attendees: List[EventAttendee] = Field(default_factory=list)
    reminders: List[Reminder] = Field(default_factory=list)
    visibility: EventVisibility = EventVisibility.DEFAULT
    color_id: Optional[str] = None
    creator_email: Optional[str] = None
    organizer_email: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    
    # StyleX-specific fields
    outfit_suggestion: Optional[str] = None
    event_type: Optional[str] = None


class CalendarListRequest(BaseModel):
    """Request for listing calendar events"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_results: int = Field(default=50, ge=1, le=250)
    include_cancelled: bool = False


class CalendarMonthView(BaseModel):
    """Month view of calendar events"""
    year: int
    month: int
    events: List[CalendarEvent]
    total_events: int
    has_more: bool = False


class CalendarDayView(BaseModel):
    """Single day calendar view"""
    date: date
    events: List[CalendarEvent]
    weather_summary: Optional[dict] = None
    outfit_of_the_day: Optional[str] = None


class OAuthState(BaseModel):
    """OAuth state for security"""
    state: str
    redirect_uri: str
    user_id: Optional[str] = None


class OAuthTokens(BaseModel):
    """OAuth tokens response"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str = "Bearer"
    scope: str


class UserCalendarSettings(BaseModel):
    """User's calendar settings"""
    user_id: str
    calendar_id: str = "primary"
    default_reminder_minutes: int = 30
    auto_outfit_suggestions: bool = True
    sync_enabled: bool = True
    timezone: str = "UTC"
    notification_preferences: dict = Field(default_factory=dict)


class EventWithOutfit(BaseModel):
    """Calendar event with AI-generated outfit suggestion"""
    event: CalendarEvent
    outfit_suggestion: Optional[str] = None
    weather_at_event: Optional[dict] = None
    recommended_colors: Optional[List[str]] = None
