import axios from 'axios';

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

// Request interceptor - Add auth token
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

// Response interceptor - Handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - redirect to auth
      localStorage.removeItem('authToken');
      window.location.href = '/auth';
    }
    return Promise.reject(error);
  }
);

export default api;

// ========================================
// AUTH API
// Used on: /auth
// ========================================
export const authApi = {
  // Authenticate with Google OAuth token
  googleAuth: (googleToken) =>
    api.post('/auth/google', { token: googleToken }),
  
  // Logout user
  logout: () => api.post('/auth/logout'),
  
  // Refresh access token
  refreshToken: () => api.post('/auth/refresh'),
};

// ========================================
// USER PROFILE API
// Used on: /profile, /dashboard, /recommendation
// ========================================
export const userApi = {
  // Get current user profile
  getProfile: () => api.get('/user/profile'),
  
  // Update user profile
  updateProfile: (data) => api.patch('/user/profile', data),
  
  // Upload and analyze selfie
  uploadSelfie: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/face-analysis/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  // Get user preferences
  getPreferences: () => api.get('/user/preferences'),
  
  // Update user preferences
  updatePreferences: (data) => api.patch('/user/preferences', data),
  
  // Delete account
  deleteAccount: () => api.delete('/user/account'),
};

// ========================================
// FACE/BODY ANALYSIS API
// Used on: /onboarding
// ========================================
export const analysisApi = {
  // Analyze face for skin tone, undertone, and demographics
  analyzeFace: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/face-analysis/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  // Get skin tone analysis only
  getSkinTone: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/face-analysis/skin-tone', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  // Get undertone analysis
  getUndertone: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/face-analysis/undertone', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// ========================================
// CLOTHING ANALYSIS API
// Used for analyzing user's wardrobe items
// ========================================
export const clothingApi = {
  // Analyze a clothing item
  analyzeClothing: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/cloth-analysis/analyze', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  // Get user's wardrobe
  getWardrobe: () => api.get('/clothing/wardrobe'),
  
  // Add item to wardrobe
  addToWardrobe: (data) => api.post('/clothing/wardrobe', data),
  
  // Remove item from wardrobe
  removeFromWardrobe: (id) => api.delete(`/clothing/wardrobe/${id}`),
};

// ========================================
// RECOMMENDATION API
// Used on: /dashboard, /recommendation
// ========================================
export const recommendationApi = {
  // Generate outfit recommendations
  generate: (params) =>
    api.post('/recommendation/generate', params),
  
  // Get recommendation by ID
  getById: (id) => api.get(`/recommendation/${id}`),
  
  // Get recommendation history
  getHistory: (params) =>
    api.get('/recommendation/history', { params }),
  
  // Save/favorite an outfit
  saveOutfit: (id) => api.post(`/recommendation/${id}/save`),
  
  // Unsave outfit
  unsaveOutfit: (id) => api.delete(`/recommendation/${id}/save`),
  
  // Get saved outfits
  getSavedOutfits: () => api.get('/recommendation/saved'),
  
  // Rate an outfit
  rateOutfit: (id, rating) =>
    api.post(`/recommendation/${id}/rate`, { rating }),
};

// ========================================
// CALENDAR API
// Used on: /calendar, /dashboard
// ========================================
export const calendarApi = {
  // Get all events
  getEvents: (params) => api.get('/calendar/events', { params }),
  
  // Get single event
  getEvent: (id) => api.get(`/calendar/events/${id}`),
  
  // Create event
  createEvent: (data) => api.post('/calendar/events', data),
  
  // Update event
  updateEvent: (id, data) => api.put(`/calendar/events/${id}`, data),
  
  // Delete event
  deleteEvent: (id) => api.delete(`/calendar/events/${id}`),
  
  // Get outfit for event
  getEventOutfit: (id) => api.get(`/calendar/events/${id}/outfit`),
  
  // Regenerate outfit for event
  regenerateEventOutfit: (id) =>
    api.post(`/calendar/events/${id}/outfit/regenerate`),
};

// ========================================
// VIRTUAL TRY-ON API
// Used for trying on outfits virtually
// ========================================
export const tryOnApi = {
  // Try on a garment
  tryOn: (userImage, garmentImage) => {
    const formData = new FormData();
    formData.append('user_image', userImage);
    formData.append('garment_image', garmentImage);
    return api.post('/virtual-tryon/try-on', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  // Get try-on history
  getHistory: () => api.get('/virtual-tryon/history'),
};

// ========================================
// WEATHER API (External Integration)
// ========================================
export const weatherApi = {
  // Get current weather by coordinates
  getCurrent: (lat, lon) =>
    api.get('/weather/current', { params: { lat, lon } }),
  
  // Get weather forecast
  getForecast: (lat, lon, days = 7) =>
    api.get('/weather/forecast', { params: { lat, lon, days } }),
};
