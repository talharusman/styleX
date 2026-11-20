import axios from 'axios';

// =============================================================================
// StyleX Frontend API Integration
// =============================================================================
// This file contains all API integrations with the StyleX backend.
// Refer to frontendBackend.md for complete API documentation.
// Base URL: http://localhost:8000 (Development) | https://api.stylex.com (Production)
// =============================================================================

// Base API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Single in-flight refresh shared by all concurrent 401s. Refresh tokens rotate
// (each is single-use), so parallel refreshes would trip reuse detection.
let refreshPromise = null;

const clearSession = () => {
  localStorage.removeItem('authToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('userId');
  localStorage.removeItem('auth-storage');
};

const refreshTokens = () => {
  if (!refreshPromise) {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) return Promise.reject(new Error('No refresh token'));
    refreshPromise = axios
      .post(`${API_BASE_URL}/api/auth/refresh`, { refresh_token: refreshToken })
      .then(({ data }) => {
        localStorage.setItem('authToken', data.access_token);
        if (data.refresh_token) {
          localStorage.setItem('refreshToken', data.refresh_token);
        }
        return data.access_token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
};

// Response interceptor - Handle errors globally and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isAuthEndpoint = originalRequest?.url?.startsWith('/api/auth/');

    // 401 on a normal request: try to refresh once, then retry.
    // Auth endpoints (login/register/refresh) are excluded: a wrong password is not an expired session.
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      try {
        const accessToken = await refreshTokens();
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        clearSession();
        if (window.location.pathname !== '/auth') {
          window.location.href = '/auth';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// =============================================================================
// AUTHENTICATION API (/api/auth)
// Endpoints: register, login, refresh, me, logout
// Used on: /auth page
// =============================================================================
export const authApi = {
  /**
   * Register a new user
   * POST /api/auth/register
   * @param {Object} data - { email, password, name }
   * @returns {Object} { success, message, user: { user_id, email, name, roles } }
   */
  register: (data) => api.post('/api/auth/register', data),

  /**
   * Login with email/password
   * POST /api/auth/login
   * @param {Object} data - { email, password }
   * @returns {Object} { success, access_token, refresh_token, token_type, expires_in }
   */
  login: (data) => api.post('/api/auth/login', data),

  /**
   * Refresh access token
   * POST /api/auth/refresh
   * @param {string} refreshToken - Current refresh token
   * @returns {Object} { success, access_token, refresh_token, token_type, expires_in }
   */
  refreshToken: (refreshToken) =>
    api.post('/api/auth/refresh', { refresh_token: refreshToken }),

  /**
   * Get current authenticated user
   * GET /api/auth/me
   * Requires: Authorization header
   * @returns {Object} { success, message, user: { user_id, email, name, roles } }
   */
  getCurrentUser: () => api.get('/api/auth/me'),

  /**
   * Logout user
   * POST /api/auth/logout
   * Requires: Authorization header
   */
  logout: () => api.post('/api/auth/logout'),
};

// =============================================================================
// WEATHER API (/api/weather)
// Endpoints: current weather, forecast, outfit suggestion
// Used on: /dashboard page
// =============================================================================
export const weatherApi = {
  /**
   * Get current weather by location
   * GET /api/weather?location={location}&units={units}
   * @param {string} location - City name (e.g., "London")
   * @param {string} units - Temperature units: "celsius" | "fahrenheit"
   * @returns {Object} { location, temperature, feels_like, condition, humidity, 
   *                     wind_speed, icon, outfit_suggestions, weather_advice, recommended_colors }
   */
  getCurrent: (location, units = 'celsius') =>
    api.get('/api/weather', { params: { location, units } }),

  /**
   * Get current weather by coordinates (alternative method)
   * Uses location name derived from coordinates
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @param {string} units - Temperature units
   */
  getCurrentByCoords: async (lat, lon, units = 'celsius') => {
    // Note: Backend expects location name, not coordinates
    // In production, use a reverse geocoding service to get location name
    // For now, we'll use a default or the user's saved location
    try {
      // Attempt to reverse geocode using browser's built-in API or fallback
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`
      );
      const data = await response.json();
      const location = data.address?.city || data.address?.town || 'London';
      return api.get('/api/weather', { params: { location, units } });
    } catch {
      // Fallback to default location
      return api.get('/api/weather', { params: { location: 'London', units } });
    }
  },

  /**
   * Get weather forecast
   * GET /api/weather/forecast?location={location}&days={days}
   * @param {string} location - City name
   * @param {number} days - Number of forecast days (1-7)
   * @returns {Object} Forecast data
   */
  getForecast: (location, days = 5) =>
    api.get('/api/weather/forecast', { params: { location, days } }),

  /**
   * Get outfit suggestion based on weather
   * GET /api/weather/outfit-suggestion?temperature={temp}&condition={condition}&humidity={humidity}
   * @param {number} temperature - Current temperature
   * @param {string} condition - Weather condition (sunny, cloudy, etc.)
   * @param {number} humidity - Humidity percentage
   */
  getOutfitSuggestion: (temperature, condition, humidity) =>
    api.get('/api/weather/outfit-suggestion', {
      params: { temperature, condition, humidity },
    }),
};

// =============================================================================
// GROQ CHAT AI API (/api/chat)
// Endpoints: chat, style-advice, weather-outfit, event-outfit
// Used on: Chat interface, Dashboard AI recommendations
// =============================================================================
export const chatApi = {
  /**
   * Basic chat with AI
   * POST /api/chat
   * @param {Object} data - { message, context_type, user_context }
   * @returns {Object} { response, tokens_used, model }
   */
  chat: (data) => api.post('/api/chat', data),

  /**
   * Get personalized style advice
   * POST /api/chat/style-advice
   * @param {Object} data - { query, body_type, skin_tone, style_preference }
   * @returns {Object} { advice, outfit_suggestions, color_palette, confidence_score }
   */
  getStyleAdvice: (data) => api.post('/api/chat/style-advice', data),

  /**
   * Get weather-appropriate outfit
   * POST /api/chat/weather-outfit
   * @param {Object} data - { weather_data: { temperature, condition, humidity }, style_preference }
   * @returns {Object} Outfit recommendations
   */
  getWeatherOutfit: (data) => api.post('/api/chat/weather-outfit', data),

  /**
   * Get outfit for specific event
   * POST /api/chat/event-outfit
   * @param {Object} data - { event_title, event_time, location }
   * @returns {Object} Event-appropriate outfit recommendations
   */
  getEventOutfit: (data) => api.post('/api/chat/event-outfit', data),
};

// =============================================================================
// GOOGLE CALENDAR API (/api/calendar)
// Endpoints: OAuth, events CRUD, month view, outfit suggestions
// Used on: /calendar page
// =============================================================================
export const calendarApi = {
  /**
   * Start Google OAuth flow
   * GET /api/calendar/auth?redirect_url={redirectUrl}
   * @param {string} redirectUrl - URL to redirect after OAuth
   * @returns {Object} { auth_url, state }
   */
  startOAuth: (redirectUrl) =>
    api.get('/api/calendar/auth', { params: { redirect_url: redirectUrl } }),

  /**
   * List calendar events
   * GET /api/calendar?user_id={userId}
   * @param {string} userId - User ID
   * @param {Object} params - Additional filters (start, end dates)
   * @returns {Object} { events: [...] }
   */
  getEvents: (userId, params = {}) =>
    api.get('/api/calendar', { params: { user_id: userId, ...params } }),

  /**
   * Get month view of events
   * GET /api/calendar/month/{year}/{month}?user_id={userId}
   * @param {number} year - Year (e.g., 2026)
   * @param {number} month - Month (1-12)
   * @param {string} userId - User ID
   */
  getMonthView: (year, month, userId) =>
    api.get(`/api/calendar/month/${year}/${month}`, { params: { user_id: userId } }),

  /**
   * Create a new event
   * POST /api/calendar
   * @param {Object} data - { user_id, title, start_time, end_time, location }
   * @returns {Object} Created event
   */
  createEvent: (data) => api.post('/api/calendar', data),

  /**
   * Update an event
   * PUT /api/calendar/{eventId}
   * @param {string} eventId - Event ID
   * @param {Object} data - Updated event data
   */
  updateEvent: (eventId, data) => api.put(`/api/calendar/${eventId}`, data),

  /**
   * Delete an event
   * DELETE /api/calendar/{eventId}
   * @param {string} eventId - Event ID
   */
  deleteEvent: (eventId) => api.delete(`/api/calendar/${eventId}`),

  /**
   * Get outfit suggestion for event
   * GET /api/calendar/{eventId}/outfit?user_id={userId}
   * @param {string} eventId - Event ID
   * @param {string} userId - User ID
   * @returns {Object} Outfit suggestion for the event
   */
  getEventOutfit: (eventId, userId) =>
    api.get(`/api/calendar/${eventId}/outfit`, { params: { user_id: userId } }),
};

// =============================================================================
// FACE ANALYSIS API (/api/face-analysis)
// Endpoints: analyze, upload, color-palette
// Used on: /onboarding page (selfie step)
// =============================================================================
export const faceAnalysisApi = {
  /**
   * Analyze face from base64 image
   * POST /api/face-analysis/analyze
   * @param {string} imageBase64 - Base64 encoded image data
   * @returns {Object} { success, skin_features, facial_features, color_recommendations, style_tips, processing_time_ms }
   */
  analyze: (imageBase64) =>
    api.post('/api/face-analysis/analyze', { image_base64: imageBase64 }),

  /**
   * Upload and analyze face image
   * POST /api/face-analysis/analyze/upload
   * @param {File} file - Image file
   * @returns {Object} Same as analyze endpoint
   */
  analyzeUpload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/face-analysis/analyze/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /**
   * Get color palette for seasonal type
   * GET /api/face-analysis/color-palette/{seasonalType}
   * @param {string} seasonalType - "spring" | "summer" | "autumn" | "winter"
   * @returns {Object} Color palette recommendations
   */
  getColorPalette: (seasonalType) =>
    api.get(`/api/face-analysis/color-palette/${seasonalType}`),
};

// Keep the old name for backward compatibility
export const analysisApi = faceAnalysisApi;

// =============================================================================
// CLOTH ANALYSIS API (/cloth-analysis)
// Endpoints: analyze clothing items
// Used on: Wardrobe management, outfit analysis
// =============================================================================
export const clothAnalysisApi = {
  /**
   * Analyze clothing item from base64 image
   * POST /cloth-analysis/analyze
   * @param {string} imageBase64 - Base64 encoded image
   * @returns {Object} { success, features: { dominant_colors, category, gender, style, 
   *                     design_pattern, fabric_type, weather_suitability, formality_level, confidence } }
   */
  analyze: (imageBase64) =>
    api.post('/cloth-analysis/analyze', { image_base64: imageBase64 }),

  /**
   * Analyze clothing item from uploaded file
   * POST /cloth-analysis/analyze
   * @param {File} file - Image file
   */
  analyzeUpload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/cloth-analysis/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Keep old name for backward compatibility
export const clothingApi = {
  analyzeClothing: clothAnalysisApi.analyzeUpload,
  // Note: These endpoints may need backend implementation
  getWardrobe: () => api.get('/clothing/wardrobe'),
  addToWardrobe: (data) => api.post('/clothing/wardrobe', data),
  removeFromWardrobe: (id) => api.delete(`/clothing/wardrobe/${id}`),
};

// =============================================================================
// RECOMMENDATION API (/recommendation)
// Endpoints: recommend outfits based on skin features and available clothes
// Used on: /dashboard, /recommendation pages
// =============================================================================
export const recommendationApi = {
  /**
   * Get outfit recommendations
   * POST /recommendation/recommend
   * @param {Object} data - { skin_features, available_clothes, top_k }
   * @returns {Object} { recommendations, detected_season, best_colors }
   */
  recommend: (data) => api.post('/recommendation/recommend', data),

  /**
   * Generate outfit recommendations (alias for UI compatibility)
   * Uses the recommend endpoint with simplified parameters
   * @param {Object} params - { weather, events, regenerate }
   */
  generate: (params) => api.post('/recommendation/recommend', params),

  /**
   * Get recommendation by ID
   * Note: This endpoint may need backend implementation
   * @param {string} id - Recommendation ID
   */
  getById: (id) => api.get(`/recommendation/${id}`),

  /**
   * Save/favorite an outfit
   * @param {string} id - Outfit ID
   */
  saveOutfit: (id) => api.post(`/recommendation/${id}/save`),

  /**
   * Unsave/unfavorite an outfit
   * @param {string} id - Outfit ID
   */
  unsaveOutfit: (id) => api.delete(`/recommendation/${id}/save`),

  /**
   * Get saved outfits
   */
  getSavedOutfits: () => api.get('/recommendation/saved'),

  /**
   * Rate an outfit
   * @param {string} id - Outfit ID
   * @param {number} rating - Rating value
   */
  rateOutfit: (id, rating) => api.post(`/recommendation/${id}/rate`, { rating }),
};

// =============================================================================
// ONBOARDING API (/api/onboarding)
// Endpoints: steps, progress, submit step data, complete
// Used on: /onboarding page
// =============================================================================
export const onboardingApi = {
  /**
   * Get onboarding steps
   * GET /api/onboarding/steps
   * @returns {Object} { steps: [{ step, name, title }, ...] }
   */
  getSteps: () => api.get('/api/onboarding/steps'),

  /**
   * Get user's onboarding progress
   * GET /api/onboarding/progress/{userId}
   * @param {string} userId - User ID
   */
  getProgress: (userId) => api.get(`/api/onboarding/progress/${userId}`),

  /**
   * Submit body type selection
   * POST /api/onboarding/step/body-type/{userId}
   * @param {string} userId - User ID
   * @param {Object} data - { body_type }
   */
  submitBodyType: (userId, data) =>
    api.post(`/api/onboarding/step/body-type/${userId}`, data),

  /**
   * Submit skin tone selection
   * POST /api/onboarding/step/skin-tone/{userId}
   * @param {string} userId - User ID
   * @param {Object} data - { skin_tone }
   */
  submitSkinTone: (userId, data) =>
    api.post(`/api/onboarding/step/skin-tone/${userId}`, data),

  /**
   * Submit style preferences
   * POST /api/onboarding/step/style/{userId}
   * @param {string} userId - User ID
   * @param {Object} data - { style_preference, color_preferences }
   */
  submitStyle: (userId, data) =>
    api.post(`/api/onboarding/step/style/${userId}`, data),

  /**
   * Complete onboarding
   * POST /api/onboarding/step/complete/{userId}
   * @param {string} userId - User ID
   */
  complete: (userId) => api.post(`/api/onboarding/step/complete/${userId}`, {}),
};

// =============================================================================
// DASHBOARD API (/api/dashboard)
// Endpoints: dashboard data, outfit of the day, outfit carousel
// Used on: /dashboard page
// =============================================================================
export const dashboardApi = {
  /**
   * Get dashboard data
   * GET /api/dashboard?user_id={userId}&location={location}
   * @param {string} userId - User ID
   * @param {string} location - Location for weather
   * @returns {Object} { greeting, weather, upcoming_events, outfit_of_the_day, style_tip }
   */
  getDashboard: (userId, location) =>
    api.get('/api/dashboard', { params: { user_id: userId, location } }),

  /**
   * Get outfit of the day
   * GET /api/dashboard/outfit-of-the-day?user_id={userId}
   * @param {string} userId - User ID
   */
  getOutfitOfTheDay: (userId) =>
    api.get('/api/dashboard/outfit-of-the-day', { params: { user_id: userId } }),

  /**
   * Get outfit carousel/suggestions
   * GET /api/dashboard/outfits?user_id={userId}&limit={limit}
   * @param {string} userId - User ID
   * @param {number} limit - Number of outfits to return
   */
  getOutfitCarousel: (userId, limit = 5) =>
    api.get('/api/dashboard/outfits', { params: { user_id: userId, limit } }),
};

// =============================================================================
// PROFILE API (/api/profile)
// Endpoints: get, update, style profile, color recommendations
// Used on: /profile page
// =============================================================================
export const profileApi = {
  /**
   * Get user profile
   * GET /api/profile/{userId}
   * @param {string} userId - User ID
   * @returns {Object} { user_id, email, name, body_type, skin_tone, style_preference, 
   *                     gender, onboarding_complete, subscription, created_at }
   */
  getProfile: (userId) => api.get(`/api/profile/${userId}`),

  /**
   * Update user profile
   * PATCH /api/profile/{userId}
   * @param {string} userId - User ID
   * @param {Object} data - Profile fields to update
   */
  updateProfile: (userId, data) => api.patch(`/api/profile/${userId}`, data),

  /**
   * Get style profile
   * GET /api/profile/{userId}/style
   * @param {string} userId - User ID
   */
  getStyleProfile: (userId) => api.get(`/api/profile/${userId}/style`),

  /**
   * Get color recommendations based on user's features
   * GET /api/profile/{userId}/color-recommendations
   * @param {string} userId - User ID
   */
  getColorRecommendations: (userId) =>
    api.get(`/api/profile/${userId}/color-recommendations`),
};

// Keep old userApi for backward compatibility
export const userApi = {
  getProfile: () => {
    // Note: This needs the user ID from auth store
    // For now, use the /api/auth/me endpoint
    return api.get('/api/auth/me');
  },
  updateProfile: (data) => {
    // Note: This needs the user ID - should be passed from component
    // Assuming user_id is in the data or from auth store
    const userId = data.user_id || localStorage.getItem('userId');
    return api.patch(`/api/profile/${userId}`, data);
  },
  getPreferences: () => api.get('/user/preferences'),
  updatePreferences: (data) => api.patch('/user/preferences', data),
  deleteAccount: () => api.delete('/user/account'),
};

// =============================================================================
// SETTINGS API (/api/settings)
// Endpoints: get settings, update notifications/privacy/appearance, export/delete data
// Used on: /settings page
// =============================================================================
export const settingsApi = {
  /**
   * Get all user settings
   * GET /api/settings/{userId}
   * @param {string} userId - User ID
   * @returns {Object} { account, notifications, privacy, appearance, calendar, ai }
   */
  getSettings: (userId) => api.get(`/api/settings/${userId}`),

  /**
   * Update notification settings
   * PATCH /api/settings/{userId}/notifications
   * @param {string} userId - User ID
   * @param {Object} data - { daily_outfit, weather_alerts, event_reminders, push_enabled }
   */
  updateNotifications: (userId, data) =>
    api.patch(`/api/settings/${userId}/notifications`, data),

  /**
   * Update privacy settings
   * PATCH /api/settings/{userId}/privacy
   * @param {string} userId - User ID
   * @param {Object} data - Privacy settings
   */
  updatePrivacy: (userId, data) =>
    api.patch(`/api/settings/${userId}/privacy`, data),

  /**
   * Update appearance settings
   * PATCH /api/settings/{userId}/appearance
   * @param {string} userId - User ID
   * @param {Object} data - { theme, language }
   */
  updateAppearance: (userId, data) =>
    api.patch(`/api/settings/${userId}/appearance`, data),

  /**
   * Export user data (GDPR)
   * GET /api/settings/{userId}/export
   * @param {string} userId - User ID
   */
  exportData: (userId) => api.get(`/api/settings/${userId}/export`),

  /**
   * Delete user data (GDPR)
   * DELETE /api/settings/{userId}/data
   * @param {string} userId - User ID
   */
  deleteData: (userId) => api.delete(`/api/settings/${userId}/data`),
};

// =============================================================================
// VIRTUAL TRY-ON API (/virtual-tryon)
// Endpoints: try-on, history
// Used on: Virtual try-on feature
// =============================================================================
export const virtualTryOnApi = {
  /**
   * Try on a garment virtually
   * POST /virtual-tryon/try-on
   * @param {File} userImage - User's photo
   * @param {File} garmentImage - Garment to try on
   */
  tryOn: (userImage, garmentImage) => {
    const formData = new FormData();
    formData.append('user_image', userImage);
    formData.append('garment_image', garmentImage);
    return api.post('/virtual-tryon/try-on', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /**
   * Get try-on history
   * GET /virtual-tryon/history
   */
  getHistory: () => api.get('/virtual-tryon/history'),
};

// Keep old name for backward compatibility
export const tryOnApi = virtualTryOnApi;

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Convert file to base64
 * @param {File} file - File to convert
 * @returns {Promise<string>} Base64 string without data URL prefix
 */
export const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      // Remove the data URL prefix (e.g., "data:image/jpeg;base64,")
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = (error) => reject(error);
  });
};

/**
 * Parse API error response
 * @param {Error} error - Axios error object
 * @returns {Object} { message, code, details }
 */
export const parseApiError = (error) => {
  if (error.response?.data) {
    return {
      message: error.response.data.message || 'An error occurred',
      code: error.response.data.code || error.response.status,
      details: error.response.data.details || null,
    };
  }
  return {
    message: error.message || 'Network error',
    code: 0,
    details: null,
  };
};

// =============================================================================
// WARDROBE API (/api/wardrobe)
// Per-user clothing items, ranking against the stored skin profile, saved outfits.
// All endpoints require authentication and only return the caller's data.
// Used on: /wardrobe
// =============================================================================
export const wardrobeApi = {
  /** POST /api/wardrobe/items (multipart) - upload + analyze a clothing photo */
  addItem: (file, name) => {
    const form = new FormData();
    form.append('file', file);
    if (name) form.append('name', name);
    return api.post('/api/wardrobe/items', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // first analysis can load models
    });
  },
  /** GET /api/wardrobe/items?category=&favorite=&needs_review= */
  listItems: (params = {}) => api.get('/api/wardrobe/items', { params }),
  /** PATCH /api/wardrobe/items/{id} - correct analysis results */
  updateItem: (id, data) => api.patch(`/api/wardrobe/items/${id}`, data),
  /** POST /api/wardrobe/items/{id}/favorite - toggle */
  toggleFavorite: (id) => api.post(`/api/wardrobe/items/${id}/favorite`),
  /** DELETE /api/wardrobe/items/{id} */
  deleteItem: (id) => api.delete(`/api/wardrobe/items/${id}`),
  /** GET item photo as a Blob (the image endpoint is authenticated) */
  getImage: (imageUrl) => api.get(imageUrl, { responseType: 'blob' }),
  /** GET /api/wardrobe/recommendations - ranked wardrobe */
  recommendations: (params = {}) => api.get('/api/wardrobe/recommendations', { params }),
  /** GET /api/wardrobe/outfits - complete outfit combinations */
  outfits: (params = {}) => api.get('/api/wardrobe/outfits', { params }),
  /** POST /api/wardrobe/outfits/saved */
  saveOutfit: (data) => api.post('/api/wardrobe/outfits/saved', data),
  /** GET /api/wardrobe/outfits/saved */
  savedOutfits: () => api.get('/api/wardrobe/outfits/saved'),
  /** DELETE /api/wardrobe/outfits/saved/{id} */
  deleteSavedOutfit: (id) => api.delete(`/api/wardrobe/outfits/saved/${id}`),
};
