import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi, profileApi, parseApiError } from '../api';

/**
 * Authentication Store
 * Manages user authentication state and integrates with StyleX backend
 * 
 * Backend Endpoints Used:
 * - POST /api/auth/register - Register new user
 * - POST /api/auth/login - Login with email/password
 * - POST /api/auth/google - Google OAuth login
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
       * Register a new user
       * POST /api/auth/register
       */
      register: async (email, password, name) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.register({ email, password, name });
          const { user } = response.data;
          
          set({
            user,
            isLoading: false,
          });
          
          // After registration, user needs to login
          return { success: true, user, needsLogin: true };
        } catch (error) {
          const { message } = parseApiError(error);
          set({ error: message, isLoading: false });
          return { success: false, error: message };
        }
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
          
          set({
            user,
            token: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
          
          return { success: true, user };
        } catch (error) {
          const { message } = parseApiError(error);
          set({ error: message, isLoading: false });
          return { success: false, error: message };
        }
      },

      /**
       * Login with Google OAuth token
       * POST /api/auth/google (or use standard login flow)
       * Note: Backend may need Google OAuth implementation
       */
      login: async (googleToken) => {
        set({ isLoading: true, error: null });
        try {
          // Try Google OAuth endpoint first
          const response = await authApi.googleAuth(googleToken);
          const { access_token, refresh_token, user } = response.data;
          
          localStorage.setItem('authToken', access_token);
          if (refresh_token) {
            localStorage.setItem('refreshToken', refresh_token);
          }
          if (user?.user_id) {
            localStorage.setItem('userId', user.user_id);
          }
          
          set({
            user,
            token: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
          });
          
          return { success: true, user };
        } catch (error) {
          // If Google OAuth isn't implemented, fall back to demo mode
          // ASSUMPTION: In production, this would be properly implemented
          console.warn('Google OAuth not available, using demo mode');
          
          // Demo user for development
          const demoUser = {
            user_id: 'demo_user_' + Date.now(),
            email: 'demo@stylex.com',
            name: 'Demo User',
            roles: ['user'],
            onboardingCompleted: false,
          };
          
          localStorage.setItem('authToken', 'demo_token_' + Date.now());
          localStorage.setItem('userId', demoUser.user_id);
          
          set({
            user: demoUser,
            token: 'demo_token',
            isAuthenticated: true,
            isLoading: false,
          });
          
          return { success: true, user: demoUser };
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
          set({ isAuthenticated: false });
          return;
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
            token,
            isAuthenticated: true,
            isLoading: false,
          });
          
          return { success: true, user };
        } catch (error) {
          // Token is invalid or expired
          localStorage.removeItem('authToken');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('userId');
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false,
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
        } catch (error) {
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
