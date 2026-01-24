# StyleX Backend Integration Guide

This document describes how to integrate the new modules with your existing backend.

---

## New Modules Created

| Module | Path | Description |
|--------|------|-------------|
| `groq_chat` | `/app/groq_chat/` | AI chatbot with Groq LLM |
| `weather` | `/app/weather/` | Weather API integration |
| `calendar` | `/app/calendar/` | Google Calendar OAuth & CRUD |
| `onboarding` | `/app/onboarding/` | 5-step user onboarding wizard |
| `dashboard` | `/app/dashboard/` | Combined dashboard view |
| `profile` | `/app/profile/` | User profile management |
| `settings` | `/app/settings/` | User settings management |

---

## 1. Update `main.py`

Add the following imports and router registrations to your `main.py`:

```python
# ========== Add these imports at the top ==========
from app.groq_chat import router as groq_chat_router
from app.weather import router as weather_router
from app.calendar import router as calendar_router
from app.onboarding import router as onboarding_router
from app.dashboard import router as dashboard_router
from app.profile import router as profile_router
from app.settings import router as settings_router


# ========== Register routers (add after your existing router registrations) ==========

# AI Chatbot
app.include_router(groq_chat_router)

# Weather Integration
app.include_router(weather_router)

# Google Calendar
app.include_router(calendar_router)

# Onboarding Wizard
app.include_router(onboarding_router)

# Dashboard
app.include_router(dashboard_router)

# User Profile
app.include_router(profile_router)

# Settings
app.include_router(settings_router)
```

---

## 2. Environment Variables

Add these to your `.env` file:

```env
# Groq AI API
GROQ_API_KEY=#

# OpenWeatherMap API
OPENWEATHER_API_KEY=your_openweathermap_api_key

# Google OAuth (for Calendar)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/calendar/auth/callback
```

---

## 3. Install Dependencies

Add these to your `requirements.txt`:

```
groq>=0.4.0
httpx>=0.24.0
google-auth>=2.0.0
google-auth-oauthlib>=1.0.0
```

Then run:
```bash
pip install -r requirements.txt
```

---

## 4. Wire Up Service Dependencies

For production, you'll want to connect the services together. In `main.py` or a startup event:

```python
from contextlib import asynccontextmanager
from app.dashboard.service import get_dashboard_service
from app.weather.service import get_weather_service
from app.calendar.service import get_calendar_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect services on startup
    dashboard = get_dashboard_service()
    dashboard.set_services(
        weather_service=get_weather_service(),
        calendar_service=get_calendar_service()
    )
    yield
    # Cleanup on shutdown

app = FastAPI(lifespan=lifespan)
```

---

## 5. API Endpoints Reference

### AI Chat (`/api/chat`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Chat with AI |
| POST | `/api/chat/style-advice` | Get style advice |
| POST | `/api/chat/weather-outfit` | Get weather-based outfit |
| POST | `/api/chat/event-outfit` | Get event-based outfit |
| GET | `/api/chat/health` | Health check |

### Weather (`/api/weather`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/weather` | Get current weather + outfit suggestions |
| GET | `/api/weather/forecast` | Get multi-day forecast |
| GET | `/api/weather/search` | Search locations |
| GET | `/api/weather/outfit-suggestion` | Get outfit for weather |
| GET | `/api/weather/health` | Health check |

### Calendar (`/api/calendar`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/auth` | Start OAuth flow |
| GET | `/api/calendar/auth/callback` | OAuth callback |
| POST | `/api/calendar/auth/revoke` | Revoke access |
| GET | `/api/calendar` | List events |
| GET | `/api/calendar/month/{year}/{month}` | Month view |
| GET | `/api/calendar/day/{year}/{month}/{day}` | Day view |
| GET | `/api/calendar/upcoming` | Upcoming events |
| GET | `/api/calendar/{event_id}` | Get event |
| POST | `/api/calendar` | Create event |
| PATCH | `/api/calendar/{event_id}` | Update event |
| DELETE | `/api/calendar/{event_id}` | Delete event |
| GET | `/api/calendar/{event_id}/outfit` | Event with outfit suggestion |

### Onboarding (`/api/onboarding`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/onboarding/progress/{user_id}` | Get progress |
| GET | `/api/onboarding/summary/{user_id}` | Get summary |
| POST | `/api/onboarding/step` | Update step |
| POST | `/api/onboarding/step/selfie/{user_id}` | Submit selfie |
| POST | `/api/onboarding/step/body-type/{user_id}` | Submit body type |
| POST | `/api/onboarding/step/skin-tone/{user_id}` | Submit skin tone |
| POST | `/api/onboarding/step/style/{user_id}` | Submit style |
| POST | `/api/onboarding/step/complete/{user_id}` | Complete onboarding |
| POST | `/api/onboarding/analyze-selfie` | Analyze selfie |
| GET | `/api/onboarding/color-recommendations` | Get color recommendations |
| POST | `/api/onboarding/reset/{user_id}` | Reset progress |
| GET | `/api/onboarding/steps` | List steps |

### Dashboard (`/api/dashboard`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Get dashboard data |
| POST | `/api/dashboard` | Get dashboard (POST) |
| GET | `/api/dashboard/outfit-of-the-day` | Outfit of the day |
| GET | `/api/dashboard/outfits` | Outfit carousel |
| GET | `/api/dashboard/quick-actions` | Quick actions |
| GET | `/api/dashboard/style-tip` | Random style tip |
| GET | `/api/dashboard/greeting` | Time-based greeting |

### Profile (`/api/profile`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/profile/{user_id}` | Get profile |
| PATCH | `/api/profile/{user_id}` | Update profile |
| DELETE | `/api/profile/{user_id}` | Delete profile |
| GET | `/api/profile/{user_id}/summary` | Profile summary |
| GET | `/api/profile/{user_id}/style` | Style profile |
| PATCH | `/api/profile/{user_id}/style` | Update style |
| GET | `/api/profile/{user_id}/stats` | Profile stats |
| POST | `/api/profile/{user_id}/avatar` | Update avatar |
| POST | `/api/profile/{user_id}/subscription` | Update subscription |
| GET | `/api/profile/{user_id}/color-recommendations` | Color recommendations |

### Settings (`/api/settings`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings/{user_id}` | All settings |
| POST | `/api/settings/{user_id}/reset` | Reset settings |
| GET | `/api/settings/{user_id}/account` | Account settings |
| POST | `/api/settings/{user_id}/account/two-factor` | Enable 2FA |
| GET | `/api/settings/{user_id}/notifications` | Notification settings |
| PATCH | `/api/settings/{user_id}/notifications` | Update notifications |
| GET | `/api/settings/{user_id}/privacy` | Privacy settings |
| PATCH | `/api/settings/{user_id}/privacy` | Update privacy |
| GET | `/api/settings/{user_id}/appearance` | Appearance settings |
| PATCH | `/api/settings/{user_id}/appearance` | Update appearance |
| GET | `/api/settings/{user_id}/calendar` | Calendar settings |
| PATCH | `/api/settings/{user_id}/calendar` | Update calendar |
| POST | `/api/settings/{user_id}/calendar/disconnect` | Disconnect Google |
| GET | `/api/settings/{user_id}/ai` | AI settings |
| PATCH | `/api/settings/{user_id}/ai` | Update AI settings |
| GET | `/api/settings/help/categories` | Help categories |
| GET | `/api/settings/help/articles/{category}` | Help articles |
| POST | `/api/settings/{user_id}/support` | Contact support |
| POST | `/api/settings/{user_id}/feedback` | Submit feedback |
| GET | `/api/settings/{user_id}/export` | Export data (GDPR) |
| DELETE | `/api/settings/{user_id}/data` | Delete data (GDPR) |

---

## 6. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Google Calendar API
4. Go to Credentials → Create OAuth 2.0 Client ID
5. Set authorized redirect URI: `http://localhost:8000/api/calendar/auth/callback`
6. Copy Client ID and Secret to your `.env` file

---

## 7. Testing the Integration

After integration, test the endpoints:

```bash
# Test AI Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What should I wear today?"}'

# Test Weather
curl "http://localhost:8000/api/weather?location=London"

# Test Dashboard
curl "http://localhost:8000/api/dashboard?user_id=test&location=London"

# Test Onboarding Steps
curl http://localhost:8000/api/onboarding/steps
```

---

## 8. Database Integration (Future)

The current implementation uses in-memory storage. For production, update these files to use your database:

- `app/groq_chat/service.py` - Store conversation history
- `app/calendar/service.py` - Store user tokens
- `app/calendar/oauth.py` - Store OAuth state
- `app/onboarding/service.py` - Store onboarding progress
- `app/dashboard/service.py` - Cache dashboard data
- `app/profile/service.py` - Store user profiles
- `app/settings/service.py` - Store user settings

Replace the in-memory dicts with database queries:

```python
# Example: Update service to use database
from app.database.repositories.user_repo import UserRepository

class ProfileService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
    
    async def get_profile(self, user_id: str):
        return await self.repo.get_by_id(user_id)
```

---

## 9. CORS Configuration

If your frontend is on a different origin, ensure CORS is configured:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 10. File Structure After Integration

```
app/
├── __init__.py
├── config.py
├── main.py
├── groq_chat/          # NEW: AI Chatbot
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   └── schemas.py
├── weather/            # NEW: Weather API
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   └── schemas.py
├── calendar/           # NEW: Google Calendar
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   ├── schemas.py
│   └── oauth.py
├── onboarding/         # NEW: Onboarding Wizard
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   └── schemas.py
├── dashboard/          # NEW: Dashboard
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   └── schemas.py
├── profile/            # NEW: User Profile
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   └── schemas.py
├── settings/           # NEW: Settings
│   ├── __init__.py
│   ├── router.py
│   ├── service.py
│   └── schemas.py
├── cloth_analysis/     # EXISTING
├── face_analysis/      # EXISTING
├── recommendation/     # EXISTING
├── virtual_tryon/      # EXISTING
├── common/             # EXISTING
└── database/           # EXISTING
```

---

## Questions?

If you encounter any issues during integration, check:

1. All imports are correct
2. Environment variables are set
3. Dependencies are installed
4. CORS is configured (if applicable)
5. Google OAuth credentials are valid

The new modules are designed to be self-contained and should not conflict with existing code.
