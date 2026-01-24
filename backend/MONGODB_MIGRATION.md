# MongoDB Migration Summary

## Overview

StyleX backend has been migrated from in-memory storage to MongoDB using the **Beanie ODM** (Object Document Mapper) with async support via **Motor** driver.

## Dependencies Added

```txt
# MongoDB
motor>=3.3.2                  # Async MongoDB driver
beanie>=1.26.0               # MongoDB ODM for Pydantic
pymongo>=4.6.1               # MongoDB Python driver
passlib[bcrypt]>=1.7.4       # Password hashing
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `stylex` | Database name |
| `MONGO_MIN_POOL_SIZE` | `10` | Minimum connection pool size |
| `MONGO_MAX_POOL_SIZE` | `100` | Maximum connection pool size |

### Docker Setup

```bash
# Start MongoDB container
docker run -d \
  --name stylex-mongo \
  -p 27017:27017 \
  -v stylex_mongo_data:/data/db \
  mongo:7.0
```

## Database Structure

### Collections

| Collection | Model | Description |
|------------|-------|-------------|
| `users` | `User` | Main user accounts |
| `user_profiles` | `UserProfile` | Extended profile with style data |
| `user_settings` | `UserSettings` | Application settings |
| `user_sessions` | `UserSession` | Authentication sessions |
| `clothing_items` | `ClothingItem` | Wardrobe items |
| `analysis_results` | `AnalysisResult` | Face/clothing analysis |
| `outfit_recommendations` | `OutfitRecommendation` | Generated outfits |
| `calendar_events` | `CalendarEvent` | Calendar integration |
| `chat_messages` | `ChatMessage` | AI chat history |
| `onboarding_progress` | `OnboardingProgress` | Onboarding steps |

### Document Models

#### User
```python
{
    "_id": ObjectId,
    "email": "user@example.com",  # Unique indexed
    "password_hash": "...",
    "name": "John Doe",
    "gender": "male|female|non_binary|prefer_not_to_say",
    "status": "active|inactive|suspended|pending",
    "email_verified": false,
    "onboarding_completed": false,
    "google_id": "...",  # OAuth
    "roles": ["user"],
    "created_at": ISODate,
    "updated_at": ISODate,
    "last_login": ISODate
}
```

#### UserProfile
```python
{
    "_id": ObjectId,
    "user_id": ObjectId,  # Indexed
    "skin_features": {
        "undertone": "warm|cool|neutral",
        "depth": "fair|light|medium|tan|deep",
        "season": "spring|summer|autumn|winter"
    },
    "body_measurements": {
        "height_cm": 175.0,
        "weight_kg": 70.0,
        "body_type": "hourglass|pear|apple|..."
    },
    "style_preferences": {
        "primary_style": "casual|formal|...",
        "secondary_styles": [],
        "favorite_colors": [],
        "avoid_colors": [],
        "recommended_colors": []
    },
    "avatar_url": "...",
    "location": "..."
}
```

#### UserSettings
```python
{
    "_id": ObjectId,
    "user_id": ObjectId,  # Unique indexed
    "notifications": { ... },
    "privacy": { ... },
    "appearance": { ... },
    "google_calendar_connected": false,
    "google_access_token": "...",
    "google_refresh_token": "...",
    "ai_personality": "friendly",
    "auto_suggest_outfits": true
}
```

## Repository Pattern

### UserRepository
Location: `app/database/repositories/user_repo.py`

```python
from app.database import user_repository, get_user_repository

# Create user
user = await user_repository.create_user(
    email="user@example.com",
    password="secure123",
    name="John Doe"
)

# Get user
user = await user_repository.get_user_by_email("user@example.com")
user = await user_repository.get_user_by_id("user_id")

# Authenticate
user = await user_repository.authenticate_user(email, password)

# Update
await user_repository.update_user(user_id, name="New Name")

# Sessions
await user_repository.create_session(user_id, refresh_token, expires_days=7)
await user_repository.invalidate_session(refresh_token)
```

### ClothingRepository
Location: `app/database/repositories/clothing_repo.py`

```python
from app.database import clothing_repository, get_clothing_repository

# Create item
item = await clothing_repository.create_item(
    user_id="...",
    image_url="...",
    features=features
)

# Get wardrobe
items = await clothing_repository.get_user_wardrobe(user_id, limit=50)

# Search
items = await clothing_repository.search_items(
    user_id,
    category="top",
    style="casual",
    colors=["blue"]
)

# Stats
stats = await clothing_repository.get_wardrobe_stats(user_id)
```

### ChatRepository
Location: `app/database/repositories/chat_repo.py`

```python
from app.database import chat_repository, get_chat_repository

# Save message
await chat_repository.create_message(
    user_id="...",
    message="Hello",
    response="Hi there!",
    session_id="session_123",
    model="llama-3.3-70b"
)

# Get history
messages = await chat_repository.get_conversation_history(
    user_id, session_id=None, limit=50
)

# Get sessions
sessions = await chat_repository.get_recent_sessions(user_id, limit=10)
```

## Service Updates

### Profile Service
- `get_profile()` - Fetches from MongoDB
- `update_profile()` - Updates MongoDB documents
- `get_profile_stats()` - Aggregates from collections

### Settings Service
- All settings persisted to `user_settings` collection
- GDPR export/delete implemented

### Onboarding Service
- Progress stored in `onboarding_progress` collection
- Step data preserved across sessions

### Calendar Service
- OAuth tokens stored in `user_settings`
- Events can be cached locally

### Chat Service
- Full conversation history in `chat_messages`
- Session management for conversations

## Connection Lifecycle

```python
# app/main.py
from contextlib import asynccontextmanager
from app.database import connect_to_database, disconnect_from_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_database()
    yield
    await disconnect_from_database()

app = FastAPI(lifespan=lifespan)
```

## Health Check

```python
GET /health

{
    "status": "healthy",
    "database": {
        "status": "healthy",
        "latency_ms": 2.5
    }
}
```

## Indexes

Indexes are automatically created by Beanie based on model definitions:

- `users.email` - Unique
- `users.google_id` - Unique, sparse
- `user_profiles.user_id` - Standard
- `user_settings.user_id` - Unique
- `user_sessions.user_id` - Standard
- `user_sessions.refresh_token` - Unique
- `clothing_items.user_id` - Standard
- `chat_messages.user_id` - Standard
- `chat_messages.session_id` - Standard
- `calendar_events.user_id` - Standard
- `calendar_events.start_time` - Standard

## Running the Application

```bash
# 1. Start MongoDB
docker run -d --name stylex-mongo -p 27017:27017 mongo:7.0

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload
```

## Migration Notes

1. **No data migration needed** - Previous implementation used in-memory storage
2. **Password hashing** - Uses bcrypt via passlib
3. **Connection pooling** - Configured for production use
4. **Async throughout** - All database operations are async
5. **Beanie ODM** - Provides Pydantic model integration
