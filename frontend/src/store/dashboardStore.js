import { create } from 'zustand';
import { recommendationApi, calendarApi, weatherApi } from '../api';

const useDashboardStore = create((set, get) => ({
  // User data
  greeting: '',
  
  // Weather
  weather: null,
  weatherLoading: false,
  
  // Today's events
  todayEvents: [],
  eventsLoading: false,
  
  // Recommendations
  recommendations: [],
  recommendationsLoading: false,
  activeRecommendationIndex: 0,
  
  // Saved outfits
  savedOutfits: [],
  
  // UI State
  error: null,

  // Initialize dashboard
  initDashboard: async (userId, location) => {
    const { fetchWeather, fetchTodayEvents, generateRecommendations } = get();
    
    // Set greeting based on time of day
    const hour = new Date().getHours();
    let greeting = 'Good morning';
    if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
    else if (hour >= 17) greeting = 'Good evening';
    
    set({ greeting });
    
    // Fetch data in parallel
    await Promise.all([
      fetchWeather(location),
      fetchTodayEvents(),
      generateRecommendations(),
    ]);
  },

  // Weather
  fetchWeather: async (location) => {
    if (!location?.lat || !location?.lon) return;
    
    set({ weatherLoading: true });
    try {
      const response = await weatherApi.getCurrent(location.lat, location.lon);
      set({ weather: response.data, weatherLoading: false });
    } catch (error) {
      console.error('Weather fetch error:', error);
      set({ weatherLoading: false });
    }
  },

  // Events
  fetchTodayEvents: async () => {
    set({ eventsLoading: true });
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await calendarApi.getEvents({ date: today });
      set({ todayEvents: response.data, eventsLoading: false });
    } catch (error) {
      console.error('Events fetch error:', error);
      set({ todayEvents: [], eventsLoading: false });
    }
  },

  // Recommendations
  generateRecommendations: async (params = {}) => {
    set({ recommendationsLoading: true, error: null });
    try {
      const response = await recommendationApi.generate(params);
      set({
        recommendations: response.data,
        recommendationsLoading: false,
        activeRecommendationIndex: 0,
      });
    } catch (error) {
      console.error('Recommendations error:', error);
      set({
        error: 'Failed to generate recommendations',
        recommendationsLoading: false,
      });
    }
  },

  regenerateRecommendations: async () => {
    const { weather, todayEvents } = get();
    await get().generateRecommendations({
      weather,
      events: todayEvents,
      regenerate: true,
    });
  },

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

  // Save outfit
  saveOutfit: async (outfitId) => {
    try {
      await recommendationApi.saveOutfit(outfitId);
      const { savedOutfits, recommendations } = get();
      const outfit = recommendations.find((r) => r.id === outfitId);
      if (outfit) {
        set({ savedOutfits: [...savedOutfits, outfit] });
      }
    } catch (error) {
      console.error('Save outfit error:', error);
    }
  },

  unsaveOutfit: async (outfitId) => {
    try {
      await recommendationApi.unsaveOutfit(outfitId);
      const { savedOutfits } = get();
      set({
        savedOutfits: savedOutfits.filter((o) => o.id !== outfitId),
      });
    } catch (error) {
      console.error('Unsave outfit error:', error);
    }
  },

  // Clear error
  clearError: () => set({ error: null }),
}));

export default useDashboardStore;
