# Frontend-Backend Integration Guide

Complete API documentation for frontend developers integrating with StyleX backend.

---

## Quick Start

### Base URL
```
Development: http://localhost:8000
Production: https://api.stylex.com
```

### Authentication
All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Error Response Format
All errors return a consistent format:
```json
{
  "success": false,
  "message": "Error description",
  "code": 400,
  "details": { ... }
}
```

---

## Environment Variables

The backend requires these environment variables (`.env` file):

```env
# Application
APP_NAME=StyleX API
APP_VERSION=1.0.0
DEBUG=true
ENVIRONMENT=development

# Security
SECRET_KEY=your-super-secret-key-min-32-chars

# External APIs
GROQ_API_KEY=
OPENWEATHER_API_KEY=your_openweathermap_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/calendar/auth/callback
```

---

## API Endpoints Reference

### 1. Authentication (`/api/auth`)

#### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```
**Response (201):**
```json
{
  "success": true,
  "message": "Registration successful",
  "user": {
    "user_id": "user_abc123",
    "email": "user@example.com",
    "name": "John Doe",
    "roles": ["user"]
  }
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```
**Response (200):**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Refresh Token
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```
**Response (200):**
```json
{
  "success": true,
  "message": "User retrieved successfully",
  "user": {
    "user_id": "user_abc123",
    "email": "user@example.com",
    "name": "John Doe",
    "roles": ["user"]
  }
}
```

#### Logout
```http
POST /api/auth/logout
Authorization: Bearer <access_token>
```

---

### 2. Weather (`/api/weather`)

#### Get Current Weather
```http
GET /api/weather?location=London&units=celsius
```
**Response (200):**
```json
{
  "location": "London",
  "temperature": 22.5,
  "feels_like": 21.0,
  "condition": "sunny",
  "description": "clear sky",
  "humidity": 45,
  "wind_speed": 5.5,
  "icon": "01d",
  "outfit_suggestions": [
    {
      "category": "top",
      "items": ["light t-shirt", "short sleeve shirt"],
      "reason": "Warm and sunny"
    },
    {
      "category": "bottom",
      "items": ["chinos", "light pants"],
      "reason": "Comfortable for temperature"
    }
  ],
  "weather_advice": "Perfect weather for outdoor activities!",
  "recommended_colors": ["light blue", "white", "beige"]
}
```

#### Get Forecast
```http
GET /api/weather/forecast?location=London&days=5
```

#### Get Outfit Suggestion
```http
GET /api/weather/outfit-suggestion?temperature=22&condition=sunny&humidity=50
```

---

### 3. Groq Chat AI (`/api/chat`)

#### Basic Chat
```http
POST /api/chat
Content-Type: application/json

{
  "message": "What should I wear to a job interview?",
  "context_type": "style",
  "user_context": {
    "body_type": "athletic",
    "skin_tone": "warm",
    "style_preference": "business casual"
  }
}
```
**Response (200):**
```json
{
  "response": "For a job interview with your athletic build and warm skin tone, I recommend...",
  "tokens_used": 245,
  "model": "llama-3.3-70b-versatile"
}
```

#### Style Advice
```http
POST /api/chat/style-advice
Content-Type: application/json

{
  "query": "What colors suit warm skin tones?",
  "body_type": "athletic",
  "skin_tone": "warm",
  "style_preference": "casual"
}
```
**Response (200):**
```json
{
  "advice": "With warm undertones, earth tones complement you beautifully...",
  "outfit_suggestions": [
    "Olive green polo with khaki chinos",
    "Burnt orange sweater with dark jeans"
  ],
  "color_palette": ["olive", "coral", "gold", "terracotta", "cream"],
  "confidence_score": 0.85
}
```

#### Weather Outfit
```http
POST /api/chat/weather-outfit
Content-Type: application/json

{
  "weather_data": {
    "temperature": 22,
    "condition": "sunny",
    "humidity": 45
  },
  "style_preference": "smart casual"
}
```

#### Event Outfit
```http
POST /api/chat/event-outfit
Content-Type: application/json

{
  "event_title": "Business Meeting",
  "event_time": "10:00 AM",
  "location": "Downtown Office"
}
```

---

### 4. Google Calendar (`/api/calendar`)

#### Start OAuth Flow
```http
GET /api/calendar/auth?redirect_url=http://localhost:3000/callback
```
**Response (200):**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random_state_string"
}
```

#### List Events
```http
GET /api/calendar?user_id=user_123
Authorization: Bearer <access_token>
```
**Response (200):**
```json
{
  "events": [
    {
      "id": "event_abc123",
      "title": "Team Meeting",
      "start_time": "2026-01-25T10:00:00Z",
      "end_time": "2026-01-25T11:00:00Z",
      "location": "Conference Room A",
      "description": "Weekly sync"
    }
  ]
}
```

#### Get Month View
```http
GET /api/calendar/month/2026/1?user_id=user_123
```

#### Create Event
```http
POST /api/calendar
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_id": "user_123",
  "title": "Dinner Party",
  "start_time": "2026-01-25T19:00:00",
  "end_time": "2026-01-25T22:00:00",
  "location": "Downtown Restaurant"
}
```

#### Get Event with Outfit Suggestion
```http
GET /api/calendar/{event_id}/outfit?user_id=user_123
```

---

### 5. Face Analysis (`/api/face-analysis`)

#### Analyze Face
```http
POST /api/face-analysis/analyze
Content-Type: application/json

{
  "image_base64": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
}
```
**Response (200):**
```json
{
  "success": true,
  "skin_features": {
    "undertone": "warm",
    "skin_depth": "medium",
    "seasonal_type": "autumn",
    "lab_l": 65.0,
    "lab_a": 12.0,
    "lab_b": 18.0,
    "skin_rgb": [198, 166, 145],
    "skin_hex": "#C6A691",
    "confidence": 0.92
  },
  "facial_features": {
    "face_shape": "oval",
    "face_width": 145.5,
    "face_height": 185.3,
    "confidence": 0.8
  },
  "color_recommendations": {
    "best_colors": ["burnt orange", "olive", "rust", "gold"],
    "avoid_colors": ["pink", "fuchsia", "bright blue"],
    "neutral_colors": ["cream", "camel", "warm gray"],
    "accent_colors": ["turquoise", "tomato red"],
    "metals": ["gold", "brass", "copper"]
  },
  "style_tips": [
    "Warm earthy tones enhance your complexion",
    "Gold jewelry complements your warm undertones"
  ],
  "processing_time_ms": 245.5
}
```

#### Upload and Analyze
```http
POST /api/face-analysis/analyze/upload
Content-Type: multipart/form-data

file: <image_file>
```

#### Get Color Palette
```http
GET /api/face-analysis/color-palette/autumn
```

---

### 6. Cloth Analysis (`/cloth-analysis`)

#### Analyze Clothing
```http
POST /cloth-analysis/analyze
Content-Type: application/json

{
  "image_base64": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
}
```
**Response (200):**
```json
{
  "success": true,
  "features": {
    "dominant_colors": [
      {"color": "#4682B4", "name": "steel blue", "percentage": 65.5}
    ],
    "category": "shirt",
    "gender": "unisex",
    "style": "casual",
    "design_pattern": "solid",
    "fabric_type": "cotton",
    "weather_suitability": "all_season",
    "formality_level": 4,
    "confidence": 0.88
  },
  "processing_time_ms": 189.3
}
```

---

### 7. Recommendations (`/recommendation`)

#### Get Outfit Recommendations
```http
POST /recommendation/recommend
Content-Type: application/json

{
  "skin_features": {
    "undertone": "warm",
    "skin_depth": "medium",
    "lab_l": 65.0,
    "lab_a": 12.0,
    "lab_b": 18.0,
    "skin_rgb": [198, 166, 145],
    "confidence": 0.9
  },
  "available_clothes": [
    {
      "cloth_id": "cloth_001",
      "dominant_color_rgb": [70, 130, 180],
      "dominant_color_name": "steel blue",
      "color_hex": "#4682B4",
      "color_palette": [],
      "category": "top",
      "gender": "unisex",
      "style": "casual",
      "design": "solid",
      "fabric": "cotton",
      "weather": "all_season",
      "formality_level": 4,
      "confidence": 0.85
    }
  ],
  "top_k": 10
}
```
**Response (200):**
```json
{
  "recommendations": [
    {
      "cloth_id": "cloth_001",
      "match_score": 0.87,
      "color_compatibility": 0.9,
      "style_compatibility": 0.85,
      "reasons": [
        "Steel blue complements warm undertones",
        "Casual style matches your preference"
      ]
    }
  ],
  "detected_season": "autumn",
  "best_colors": ["olive", "burnt orange", "rust", "gold", "terracotta"]
}
```

---

### 8. Onboarding (`/api/onboarding`)

#### Get Steps
```http
GET /api/onboarding/steps
```
**Response (200):**
```json
{
  "steps": [
    {"step": 1, "name": "selfie", "title": "Upload Selfie"},
    {"step": 2, "name": "body-type", "title": "Body Type"},
    {"step": 3, "name": "skin-tone", "title": "Skin Tone"},
    {"step": 4, "name": "style", "title": "Style Preferences"},
    {"step": 5, "name": "complete", "title": "Complete"}
  ]
}
```

#### Get Progress
```http
GET /api/onboarding/progress/{user_id}
```

#### Submit Body Type
```http
POST /api/onboarding/step/body-type/{user_id}
Content-Type: application/json

{
  "body_type": "athletic"
}
```

#### Submit Skin Tone
```http
POST /api/onboarding/step/skin-tone/{user_id}
Content-Type: application/json

{
  "skin_tone": "warm"
}
```

#### Submit Style
```http
POST /api/onboarding/step/style/{user_id}
Content-Type: application/json

{
  "style_preference": "casual",
  "color_preferences": ["navy", "gray", "olive"]
}
```

#### Complete Onboarding
```http
POST /api/onboarding/step/complete/{user_id}
```

---

### 9. Dashboard (`/api/dashboard`)

#### Get Dashboard
```http
GET /api/dashboard?user_id=user_123&location=London
```
**Response (200):**
```json
{
  "greeting": "Good morning, John!",
  "weather": {
    "temperature": 22,
    "condition": "sunny",
    "outfit_suggestion": "Light layers with breathable fabrics"
  },
  "upcoming_events": [
    {
      "id": "event_123",
      "title": "Team Meeting",
      "time": "10:00 AM",
      "outfit_suggestion": "Business casual"
    }
  ],
  "outfit_of_the_day": {
    "top": "Navy polo shirt",
    "bottom": "Khaki chinos",
    "accessories": ["Brown leather belt", "Gold watch"]
  },
  "style_tip": "Layering is key for changing temperatures!"
}
```

#### Get Outfit of the Day
```http
GET /api/dashboard/outfit-of-the-day?user_id=user_123
```

#### Get Outfit Carousel
```http
GET /api/dashboard/outfits?user_id=user_123&limit=5
```

---

### 10. Profile (`/api/profile`)

#### Get Profile
```http
GET /api/profile/{user_id}
```
**Response (200):**
```json
{
  "user_id": "user_123",
  "email": "user@example.com",
  "name": "John Doe",
  "body_type": "athletic",
  "skin_tone": "warm",
  "style_preference": "casual",
  "gender": "male",
  "onboarding_complete": true,
  "subscription": "premium",
  "created_at": "2026-01-01T00:00:00Z"
}
```

#### Update Profile
```http
PATCH /api/profile/{user_id}
Content-Type: application/json

{
  "name": "John Smith",
  "style_preference": "smart casual"
}
```

#### Get Style Profile
```http
GET /api/profile/{user_id}/style
```

#### Get Color Recommendations
```http
GET /api/profile/{user_id}/color-recommendations
```

---

### 11. Settings (`/api/settings`)

#### Get All Settings
```http
GET /api/settings/{user_id}
```
**Response (200):**
```json
{
  "account": {
    "email": "user@example.com",
    "two_factor_enabled": false
  },
  "notifications": {
    "daily_outfit": true,
    "weather_alerts": true,
    "event_reminders": true,
    "push_enabled": true
  },
  "privacy": {
    "profile_visible": true,
    "share_recommendations": false
  },
  "appearance": {
    "theme": "system",
    "language": "en"
  },
  "calendar": {
    "google_connected": true,
    "reminder_time": 60
  },
  "ai": {
    "style_aggressiveness": "medium",
    "include_trending": true
  }
}
```

#### Update Notifications
```http
PATCH /api/settings/{user_id}/notifications
Content-Type: application/json

{
  "daily_outfit": false,
  "push_enabled": true
}
```

#### Export Data (GDPR)
```http
GET /api/settings/{user_id}/export
```

#### Delete Data (GDPR)
```http
DELETE /api/settings/{user_id}/data
```

---

## WebSocket Endpoints (Coming Soon)

Real-time updates for:
- Weather changes
- New outfit suggestions
- Event reminders

---

## Error Codes Reference

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 422 | Validation Error - Invalid data format |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 502 | Bad Gateway - External service error |
| 503 | Service Unavailable - AI service down |

---

## Rate Limits

| Endpoint Category | Limit |
|-------------------|-------|
| Authentication | 10 req/min |
| Chat AI | 30 req/min |
| Image Analysis | 20 req/min |
| Other | 100 req/min |

---

## Testing

### Run Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Run Tests
```bash
pytest tests/ -v
```

### Interactive Docs
Open `http://localhost:8000/docs` for Swagger UI.

---

## Frontend Integration Checklist

- [ ] Implement JWT token storage (localStorage or secure cookie)
- [ ] Add token refresh logic
- [ ] Handle unified error responses
- [ ] Implement loading states for AI endpoints
- [ ] Add offline support for cached data
- [ ] Implement image upload for face/cloth analysis
- [ ] Handle Google OAuth redirect flow
- [ ] Add real-time weather updates

---

## Support

For API issues, contact the backend team or create an issue in the repository.
