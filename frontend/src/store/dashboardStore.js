import { create } from 'zustand';
import {
  weatherApi,
  calendarApi,
  dashboardApi,
  recommendationApi,
  chatApi,
  parseApiError,
} from '../api';

/**
 * Dashboard Store
 * Manages dashboard state including weather, events, and outfit recommendations
 * 
 * Backend Endpoints Used:
 * - GET /api/dashboard - Get complete dashboard data
 * - GET /api/dashboard/outfit-of-the-day - Get daily outfit
 * - GET /api/dashboard/outfits - Get outfit carousel
 * - GET /api/weather - Get current weather
 * - GET /api/calendar - List today's events
 * - POST /recommendation/recommend - Generate recommendations
 */
const useDashboardStore = create((set, get) => ({
  // User data
  greeting: '',
  userId: null,
  
  // Weather state
  weather: null,
  weatherLoading: false,
  weatherError: null,
  
  // Today's events
  todayEvents: [],
  eventsLoading: false,
  eventsError: null,
  
  // Recommendations / Outfit of the day
  recommendations: [],
  outfitOfTheDay: null,
  recommendationsLoading: false,
  activeRecommendationIndex: 0,
  
  // Saved outfits
  savedOutfits: [],
  
  // Style tips
  styleTip: '',
  
  // Location for weather
  location: null,
  locationName: '',
  
  // UI State
  error: null,
  dashboardLoading: false,

  /**
   * Initialize dashboard with all data
   * Uses /api/dashboard endpoint or fetches individual data
   * @param {string} userId - User ID
   * @param {Object} location - { lat, lon } coordinates
   */
  initDashboard: async (userId, location) => {
    set({ dashboardLoading: true, userId, location });
    
    // Set greeting based on time of day
    const hour = new Date().getHours();
    let greeting = 'Good morning';
    if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
    else if (hour >= 17) greeting = 'Good evening';
    
    set({ greeting });
    
    // Try to get location name for weather API
    let locationName = 'London'; // Default
    if (location?.lat && location?.lon) {
      try {
        const response = await fetch(
          `https://nominatim.openstreetmap.org/reverse?format=json&lat=${location.lat}&lon=${location.lon}`
        );
        const data = await response.json();
        locationName = data.address?.city || data.address?.town || data.address?.village || 'London';
        set({ locationName });
      } catch (e) {
        console.warn('Could not get location name, using default');
      }
    }
    
    // Try unified dashboard endpoint first
    try {
      const response = await dashboardApi.getDashboard(userId, locationName);
      const dashboardData = response.data;
      
      set({
        greeting: dashboardData.greeting || greeting,
        weather: dashboardData.weather,
        todayEvents: dashboardData.upcoming_events || [],
        outfitOfTheDay: dashboardData.outfit_of_the_day,
        styleTip: dashboardData.style_tip || '',
        dashboardLoading: false,
      });
      
      // Also add outfit of the day to recommendations
      if (dashboardData.outfit_of_the_day) {
        set({ recommendations: [dashboardData.outfit_of_the_day] });
      }
      
      return;
    } catch (e) {
      // Dashboard endpoint not available, fetch individual data
      console.log('Unified dashboard not available, fetching individual data');
    }
    
    // Fetch data in parallel using individual endpoints
    const { fetchWeather, fetchTodayEvents, generateRecommendations } = get();
    
    await Promise.all([
      fetchWeather(locationName),
      fetchTodayEvents(userId),
      generateRecommendations(userId),
    ]);
    
    set({ dashboardLoading: false });
  },

  /**
   * Fetch current weather
   * GET /api/weather?location={location}&units=celsius
   * @param {string} location - City name
   */
  fetchWeather: async (location) => {
    if (!location) return;
    
    set({ weatherLoading: true, weatherError: null });
    try {
      const response = await weatherApi.getCurrent(location, 'celsius');
      const weatherData = response.data;
      
      // Transform to expected format
      const weather = {
        temp: weatherData.temperature,
        feels_like: weatherData.feels_like,
        condition: weatherData.condition,
        description: weatherData.description,
        humidity: weatherData.humidity,
        wind_speed: weatherData.wind_speed,
        icon: weatherData.icon,
        outfit_suggestions: weatherData.outfit_suggestions,
        weather_advice: weatherData.weather_advice,
        recommended_colors: weatherData.recommended_colors,
      };
      
      set({ weather, weatherLoading: false });
      return weather;
    } catch (error) {
      console.error('Weather fetch error:', error);
      const { message } = parseApiError(error);
      set({ weatherError: message, weatherLoading: false });
      
      // Fallback mock data for demo
      const mockWeather = {
        temp: 22,
        condition: 'Clear',
        humidity: 45,
      };
      set({ weather: mockWeather });
    }
  },

  /**
   * Fetch today's events
   * GET /api/calendar?user_id={userId}
   * @param {string} userId - User ID
   */
  fetchTodayEvents: async (userId) => {
    if (!userId) {
      userId = localStorage.getItem('userId');
    }
    
    set({ eventsLoading: true, eventsError: null });
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await calendarApi.getEvents(userId, { date: today });
      const events = response.data.events || response.data || [];
      
      // Transform events to expected format
      const todayEvents = events.map((event) => ({
        id: event.id,
        title: event.title,
        time: event.start_time ? new Date(event.start_time).toLocaleTimeString([], { 
          hour: '2-digit', 
          minute: '2-digit' 
        }) : '',
        type: event.type || 'casual',
        location: event.location,
        outfit: event.outfit_suggestion,
      }));
      
      set({ todayEvents, eventsLoading: false });
      return todayEvents;
    } catch (error) {
      console.error('Events fetch error:', error);
      const { message } = parseApiError(error);
      set({ eventsError: message, todayEvents: [], eventsLoading: false });
      return [];
    }
  },

  /**
   * Generate outfit recommendations
   * POST /recommendation/recommend
   * @param {Object} params - { skin_features, available_clothes, top_k }
   */
  generateRecommendations: async (params = {}) => {
    set({ recommendationsLoading: true, error: null });
    
    const userId = params.userId || get().userId || localStorage.getItem('userId');
    const { weather, todayEvents } = get();
    
    try {
      // Try to get outfit of the day first
      try {
        const outfitResponse = await dashboardApi.getOutfitOfTheDay(userId);
        if (outfitResponse.data) {
          set({ outfitOfTheDay: outfitResponse.data });
        }
      } catch (e) {
        // Outfit of the day endpoint not available
      }
      
      // Try outfit carousel
      try {
        const carouselResponse = await dashboardApi.getOutfitCarousel(userId, 5);
        if (carouselResponse.data?.length) {
          set({
            recommendations: carouselResponse.data,
            recommendationsLoading: false,
            activeRecommendationIndex: 0,
          });
          return;
        }
      } catch (e) {
        // Carousel endpoint not available
      }
      
      // Fall back to recommendation engine
      // ASSUMPTION: User's skin_features and available_clothes would come from profile/wardrobe
      const recommendRequest = {
        // These would typically come from user profile
        skin_features: params.skin_features || {
          undertone: 'warm',
          skin_depth: 'medium',
          confidence: 0.8,
        },
        // Available clothes from wardrobe (would be fetched separately in production)
        available_clothes: params.available_clothes || [],
        top_k: 5,
        // Include context
        weather_context: weather,
        events_context: todayEvents,
        regenerate: params.regenerate || false,
      };
      
      const response = await recommendationApi.recommend(recommendRequest);
      const data = response.data;
      
      set({
        recommendations: data.recommendations || [],
        recommendationsLoading: false,
        activeRecommendationIndex: 0,
      });
    } catch (error) {
      console.error('Recommendations error:', error);
      const { message } = parseApiError(error);
      set({
        error: message || 'Failed to generate recommendations',
        recommendationsLoading: false,
      });
      
      // Use mock recommendations for demo
      set({
        recommendations: [
          {
            id: 'mock_1',
            title: 'Refined Casual',
            description: 'A sophisticated blend of comfort and style.',
            colors: ['#2C3E50', '#E6DCCF', '#6B7C5A', '#0E0E0E'],
            items: [
              { category: 'Top', name: 'Linen Button-Up Shirt' },
              { category: 'Bottom', name: 'Tailored Chinos' },
              { category: 'Footwear', name: 'Suede Loafers' },
              { category: 'Accessory', name: 'Leather Belt' },
            ],
          },
        ],
      });
    }
  },

  /**
   * Regenerate recommendations with new parameters
   */
  regenerateRecommendations: async () => {
    const { weather, todayEvents, userId } = get();
    await get().generateRecommendations({
      userId,
      weather,
      events: todayEvents,
      regenerate: true,
    });
  },

  /**
   * Get AI-powered style advice
   * Uses POST /api/chat/style-advice
   */
  getStyleAdvice: async (query) => {
    try {
      const response = await chatApi.getStyleAdvice({
        query,
        style_preference: 'casual', // Would come from user profile
      });
      return response.data;
    } catch (error) {
      console.error('Style advice error:', error);
      return null;
    }
  },

  /**
   * Get weather-based outfit from AI
   * Uses POST /api/chat/weather-outfit
   */
  getWeatherOutfit: async () => {
    const { weather } = get();
    if (!weather) return null;
    
    try {
      const response = await chatApi.getWeatherOutfit({
        weather_data: {
          temperature: weather.temp,
          condition: weather.condition,
          humidity: weather.humidity,
        },
        style_preference: 'casual',
      });
      return response.data;
    } catch (error) {
      console.error('Weather outfit error:', error);
      return null;
    }
  },

  // Navigation for recommendations carousel
  setActiveRecommendation: (index) => {
    set({ activeRecommendationIndex: index });
  },

  nextRecommendation: () => {
    const { recommendations, activeRecommendationIndex } = get();
    if (activeRecommendationIndex < recommendations.length - 1) {
      set({ activeRecommendationIndex: activeRecommendationIndex + 1 });
    }
  },

  prevRecommendation: () => {
    const { activeRecommendationIndex } = get();
    if (activeRecommendationIndex > 0) {
      set({ activeRecommendationIndex: activeRecommendationIndex - 1 });
    }
  },

  /**
   * Save outfit to favorites
   * POST /recommendation/{id}/save
   */
  saveOutfit: async (outfitId) => {
    try {
      await recommendationApi.saveOutfit(outfitId);
      const { savedOutfits, recommendations } = get();
      const outfit = recommendations.find((r) => r.id === outfitId);
      if (outfit) {
        set({ savedOutfits: [...savedOutfits, { ...outfit, isSaved: true }] });
      }
      return { success: true };
    } catch (error) {
      console.error('Save outfit error:', error);
      return { success: false, error: parseApiError(error).message };
    }
  },

  /**
   * Unsave outfit from favorites
   * DELETE /recommendation/{id}/save
   */
  unsaveOutfit: async (outfitId) => {
    try {
      await recommendationApi.unsaveOutfit(outfitId);
      const { savedOutfits } = get();
      set({
        savedOutfits: savedOutfits.filter((o) => o.id !== outfitId),
      });
      return { success: true };
    } catch (error) {
      console.error('Unsave outfit error:', error);
      return { success: false, error: parseApiError(error).message };
    }
  },

  /**
   * Fetch saved outfits
   * GET /recommendation/saved
   */
  fetchSavedOutfits: async () => {
    try {
      const response = await recommendationApi.getSavedOutfits();
      set({ savedOutfits: response.data || [] });
    } catch (error) {
      console.error('Fetch saved outfits error:', error);
    }
  },

  // Clear error
  clearError: () => set({ error: null }),
  
  // Reset dashboard state
  resetDashboard: () => set({
    greeting: '',
    weather: null,
    todayEvents: [],
    recommendations: [],
    outfitOfTheDay: null,
    savedOutfits: [],
    activeRecommendationIndex: 0,
    error: null,
  }),
}));

export default useDashboardStore;
