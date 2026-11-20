import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi, parseApiError } from '../api';
import useOnboardingStore from './onboardingStore';

/**
 * Authentication Store
 * Manages user authentication state and integrates with StyleX backend
 * 
 * Backend Endpoints Used:
 * - POST /api/auth/register - Register new user
 * - POST /api/auth/login - Login with email/password
 * - POST /api/auth/refresh - Refresh access token
 * - GET /api/auth/me - Get current user
 * - POST /api/auth/logout - Logout user
 * - GET /api/profile/{userId} - Get user profile
 */
const useAuthStore = create(
  persist(
    (set, get) => ({
      // State
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      isInitialized: false,
      error: null,

      // Actions
      setUser: (user) => {
        // Store user ID for other API calls
        if (user?.user_id) {
          localStorage.setItem('userId', user.user_id);
        }
        set({ user, isAuthenticated: !!user });
      },
      
      setToken: (accessToken, refreshToken = null) => {
        localStorage.setItem('authToken', accessToken);
        if (refreshToken) {
          localStorage.setItem('refreshToken', refreshToken);
        }
        set({ token: accessToken, refreshToken, isAuthenticated: true });
      },

      /**
       * Register a new user, then sign them in
       * POST /api/auth/register -> POST /api/auth/login
       */
      register: async (email, password, name) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.register({ email, password, name });
        } catch (error) {
          const { message } = parseApiError(error);
          set({ error: message, isLoading: false });
          return { success: false, error: message };
        }
        return get().loginWithEmail(email, password);
      },

      /**
       * Login with email and password
       * POST /api/auth/login
       */
      loginWithEmail: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login({ email, password });
          const { access_token, refresh_token, success } = response.data;
          
          if (success === false) {
            throw new Error(response.data.message || 'Login failed');
          }
          
          localStorage.setItem('authToken', access_token);
          localStorage.setItem('refreshToken', refresh_token);
          
          // Fetch user details after login
          const userResponse = await authApi.getCurrentUser();
          const user = userResponse.data.user;
          
          if (user?.user_id) {
            localStorage.setItem('userId', user.user_id);
          }
          
          useOnboardingStore.getState().claimForUser(user?.user_id);
          
          set({
            user,
            token: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
          
          return { success: true, user };
        } catch (error) {
          localStorage.removeItem('authToken');
          localStorage.removeItem('refreshToken');
          const { message } = parseApiError(error);
          set({ error: message, isLoading: false });
          return { success: false, error: message };
        }
      },

      /**
       * Logout user
       * POST /api/auth/logout
       */
      logout: async () => {
        try {
          await authApi.logout();
        } catch (error) {
          console.error('Logout error:', error);
          // Continue with local logout even if server logout fails
        } finally {
          localStorage.removeItem('authToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('userId');
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
          });
        }
      },

      /**
       * Fetch current user from backend
       * GET /api/auth/me
       * Used to restore session on page load
       */
      fetchUser: async () => {
        const token = localStorage.getItem('authToken');
        if (!token) {
          set({ user: null, token: null, refreshToken: null, isAuthenticated: false, isInitialized: true });
          return { success: false };
        }

        set({ isLoading: true });
        try {
          const response = await authApi.getCurrentUser();
          const user = response.data.user;
          
          if (user?.user_id) {
            localStorage.setItem('userId', user.user_id);
          }
          
          set({
            user,
            token: localStorage.getItem('authToken'),
            isAuthenticated: true,
            isLoading: false,
            isInitialized: true,
          });
          
          return { success: true, user };
        } catch {
          // Token is invalid or expired (the API client already tried to refresh it)
          localStorage.removeItem('authToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('userId');
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
            isInitialized: true,
          });
          return { success: false };
        }
      },

      /**
       * Refresh access token
       * POST /api/auth/refresh
       */
      refreshAccessToken: async () => {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          return { success: false };
        }

        try {
          const response = await authApi.refreshToken(refreshToken);
          const { access_token, refresh_token } = response.data;
          
          localStorage.setItem('authToken', access_token);
          if (refresh_token) {
            localStorage.setItem('refreshToken', refresh_token);
          }
          
          set({
            token: access_token,
            refreshToken: refresh_token || get().refreshToken,
          });
          
          return { success: true };
        } catch {
          // Refresh failed, user needs to re-login
          get().logout();
          return { success: false };
        }
      },

      /**
       * Update local user state
       * For optimistic UI updates after profile changes
       */
      updateUser: (updates) => {
        const { user } = get();
        if (user) {
          set({ user: { ...user, ...updates } });
        }
      },

      /**
       * Get user ID helper
       * Returns the current user's ID from state or localStorage
       */
      getUserId: () => {
        const { user } = get();
        return user?.user_id || localStorage.getItem('userId');
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

export default useAuthStore;
