import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { onboardingApi, faceAnalysisApi, parseApiError } from '../api';
import { buildStepPayloads } from './onboardingMapping';

/**
 * Onboarding Store
 * Manages the multi-step onboarding flow and integrates with StyleX backend
 * 
 * Backend Endpoints Used:
 * - GET /api/onboarding/steps - Get onboarding steps
 * - GET /api/onboarding/progress/{userId} - Get user's progress
 * - POST /api/face-analysis/analyze/upload - Analyze selfie
 * - POST /api/onboarding/step/body-type/{userId} - Submit body type
 * - POST /api/onboarding/step/skin-tone/{userId} - Submit skin tone
 * - POST /api/onboarding/step/style/{userId} - Submit style preferences
 * - POST /api/onboarding/step/complete/{userId} - Complete onboarding
 * - PATCH /api/profile/{userId} - Update user profile
 */
const useOnboardingStore = create(
  persist(
    (set, get) => ({
      // Current step (1-5)
      currentStep: 1,
      totalSteps: 5,
      
      // Step 1: Auth completed
      authCompleted: false,
      ownerId: null,
      completed: false, // true once the BACKEND has accepted completion
      
      // Step 2: Selfie data from face analysis
      selfieData: null,
      faceAnalysis: null,
      skinFeatures: null,
      facialFeatures: null,
      colorRecommendations: null,
      
      // Step 3: Body type
      bodyType: null,
      height: null,
      
      // Step 4: Style preferences
      stylePreferences: [],
      favoriteColors: [],
      avoidColors: [],
      
      // Loading states
      isAnalyzing: false,
      isSaving: false,
      error: null,
      
      // Backend sync status
      syncedWithBackend: false,

      /**
       * Fetch onboarding steps from backend
       * GET /api/onboarding/steps
       */
      fetchSteps: async () => {
        try {
          const response = await onboardingApi.getSteps();
          const steps = response.data.steps;
          set({ totalSteps: steps.length });
          return steps;
        } catch (error) {
          console.log('Using default steps configuration');
          return null;
        }
      },

      /**
       * Fetch user's onboarding progress
       * GET /api/onboarding/progress/{userId}
       */
      fetchProgress: async (userId) => {
        if (!userId) {
          userId = localStorage.getItem('userId');
        }
        if (!userId) return null;
        
        try {
          const response = await onboardingApi.getProgress(userId);
          const progress = response.data;
          
          // Update local state with server progress
          if (progress.current_step) {
            set({ currentStep: progress.current_step });
          }
          if (progress.body_type) {
            set({ bodyType: progress.body_type });
          }
          if (progress.skin_tone) {
            set({
              skinFeatures: { undertone: progress.skin_tone },
            });
          }
          if (progress.style_preferences) {
            set({ stylePreferences: progress.style_preferences });
          }
          
          return progress;
        } catch (error) {
          console.log('No existing progress found');
          return null;
        }
      },

      // Navigation
      nextStep: () => {
        const { currentStep, totalSteps } = get();
        if (currentStep < totalSteps) {
          set({ currentStep: currentStep + 1 });
        }
      },

      prevStep: () => {
        const { currentStep } = get();
        if (currentStep > 1) {
          set({ currentStep: currentStep - 1 });
        }
      },

      goToStep: (step) => {
        const { totalSteps } = get();
        if (step >= 1 && step <= totalSteps) {
          set({ currentStep: step });
        }
      },

      // Tie locally persisted onboarding progress to one account.
      // A different user logging in on this browser starts clean.
      claimForUser: (userId) => {
        if (!userId) return;
        if (get().ownerId !== userId) {
          get().resetOnboarding();
          set({ ownerId: userId, completed: false });
        }
      },

      // The server is the source of truth for "has this account finished onboarding"
      syncCompletion: (completed) => set({ completed: !!completed }),

      // Step 1: Auth
      completeAuth: () => {
        set({ authCompleted: true, currentStep: 2 });
      },

      // Step 2: Selfie Analysis
      /**
       * Analyze selfie using face analysis API
       * POST /api/face-analysis/analyze/upload
       * @param {File} file - Image file to analyze
       */
      analyzeSelfie: async (file) => {
        set({ isAnalyzing: true, error: null });
        
        try {
          const response = await faceAnalysisApi.analyzeUpload(file);
          const data = response.data;
          
          if (!data.success || !data.skin_features) {
            throw new Error(data.error || data.message || 'Analysis failed');
          }
          
          // Extract analysis results
          const { skin_features, facial_features, color_recommendations } = data;
          
          // Never invent values: the backend only returns success for a real analysis,
          // so every field below comes from the analysis itself.
          const faceAnalysis = {
            skinTone: skin_features.skin_depth,
            skinToneHex: skin_features.skin_hex,
            undertone: skin_features.undertone,
            seasonalType: skin_features.seasonal_type,
            faceShape: facial_features?.face_shape ?? null,
            confidence: skin_features.confidence,
            // Raw data for API calls
            lab_l: skin_features?.lab_l,
            lab_a: skin_features?.lab_a,
            lab_b: skin_features?.lab_b,
            skin_rgb: skin_features?.skin_rgb,
          };
          
          set({
            faceAnalysis,
            skinFeatures: skin_features,
            facialFeatures: facial_features ?? null,
            colorRecommendations: color_recommendations,
            isAnalyzing: false,
          });
          
          return { success: true, data: faceAnalysis };
        } catch (error) {
          const { message } = parseApiError(error);
          set({ error: message, isAnalyzing: false });
          return { success: false, error: message };
        }
      },

      setSelfieData: (data, analysis) => {
        set({
          selfieData: data,
          faceAnalysis: analysis,
          isAnalyzing: false,
        });
      },

      setAnalyzing: (isAnalyzing) => set({ isAnalyzing }),

      // Step 3: Body type
      /**
       * Set body type and optionally sync with backend
       * POST /api/onboarding/step/body-type/{userId}
       */
      setBodyType: async (bodyType, syncNow = false) => {
        set({ bodyType });
        
        if (syncNow) {
          const userId = localStorage.getItem('userId');
          if (userId) {
            try {
              await onboardingApi.submitBodyType(userId, { body_type: bodyType });
            } catch (error) {
              console.error('Failed to sync body type:', error);
            }
          }
        }
      },
      
      setHeight: (height) => set({ height }),

      // Step 4: Style preferences
      /**
       * Set style preferences and optionally sync with backend
       * POST /api/onboarding/step/style/{userId}
       */
      setStylePreferences: async (preferences, syncNow = false) => {
        set({ stylePreferences: preferences });
        
        if (syncNow) {
          const userId = localStorage.getItem('userId');
          if (userId) {
            try {
              await onboardingApi.submitStyle(userId, {
                style_preference: preferences[0] || 'casual',
                color_preferences: get().favoriteColors,
              });
            } catch (error) {
              console.error('Failed to sync style preferences:', error);
            }
          }
        }
      },
      
      toggleStylePreference: (style) => {
        const { stylePreferences } = get();
        const exists = stylePreferences.includes(style);
        set({
          stylePreferences: exists
            ? stylePreferences.filter((s) => s !== style)
            : [...stylePreferences, style],
        });
      },

      setFavoriteColors: (colors) => set({ favoriteColors: colors }),
      setAvoidColors: (colors) => set({ avoidColors: colors }),

      // Error handling
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),

      /**
       * Complete onboarding and save all data to backend
       * POST /api/onboarding/step/complete/{userId}
       * PATCH /api/profile/{userId}
       */
      completeOnboarding: async () => {
        const userId = localStorage.getItem('userId');
        if (!userId) {
          return { success: false, error: 'You are signed out. Please sign in again.' };
        }

        set({ isSaving: true, error: null });

        const payloads = buildStepPayloads(get());
        if (!payloads.skin) {
          const error = 'Your skin analysis is missing. Go back and upload a selfie.';
          set({ error, isSaving: false });
          return { success: false, error };
        }

        try {
          // Order matters little to the backend, but every call must succeed:
          // a failed sync means the profile would be incomplete.
          await onboardingApi.submitSkinTone(userId, payloads.skin);
          if (payloads.body) await onboardingApi.submitBodyType(userId, payloads.body);
          if (payloads.style) await onboardingApi.submitStyle(userId, payloads.style);
          await onboardingApi.complete(userId);

          set({ isSaving: false, syncedWithBackend: true, completed: true });
          return { success: true };
        } catch (error) {
          const { message, details } = parseApiError(error);
          set({ error: message, isSaving: false });
          return { success: false, error: message, code: details?.error_code ?? null };
        }
      },

      // Reset onboarding
      resetOnboarding: () => {
        set({
          currentStep: 1,
          authCompleted: false,
          selfieData: null,
          faceAnalysis: null,
          skinFeatures: null,
          facialFeatures: null,
          colorRecommendations: null,
          bodyType: null,
          height: null,
          stylePreferences: [],
          favoriteColors: [],
          avoidColors: [],
          isAnalyzing: false,
          isSaving: false,
          error: null,
          syncedWithBackend: false,
        });
      },

      // Complete only once the backend accepted it (never inferred from local data)
      isComplete: () => get().completed,

      // Get all onboarding data for API submission
      getOnboardingData: () => {
        const {
          faceAnalysis,
          skinFeatures,
          facialFeatures,
          colorRecommendations,
          bodyType,
          height,
          stylePreferences,
          favoriteColors,
          avoidColors,
        } = get();

        return {
          faceAnalysis,
          skinFeatures,
          facialFeatures,
          colorRecommendations,
          bodyType,
          height,
          stylePreferences,
          favoriteColors,
          avoidColors,
        };
      },

      /**
       * Get skin features in format expected by recommendation API
       * Used when calling POST /recommendation/recommend
       */
      getSkinFeaturesForRecommendation: () => {
        const { skinFeatures, faceAnalysis } = get();
        
        if (!skinFeatures && !faceAnalysis) return null;
        
        return {
          undertone: skinFeatures?.undertone || faceAnalysis?.undertone || 'warm',
          skin_depth: skinFeatures?.skin_depth || faceAnalysis?.skinTone || 'medium',
          lab_l: skinFeatures?.lab_l || 65.0,
          lab_a: skinFeatures?.lab_a || 12.0,
          lab_b: skinFeatures?.lab_b || 18.0,
          skin_rgb: skinFeatures?.skin_rgb || [198, 166, 145],
          confidence: skinFeatures?.confidence || faceAnalysis?.confidence || 0.8,
        };
      },
    }),
    {
      name: 'onboarding-storage',
      partialize: (state) => ({
        currentStep: state.currentStep,
        authCompleted: state.authCompleted,
        ownerId: state.ownerId,
        completed: state.completed,
        faceAnalysis: state.faceAnalysis,
        skinFeatures: state.skinFeatures,
        colorRecommendations: state.colorRecommendations,
        bodyType: state.bodyType,
        height: state.height,
        stylePreferences: state.stylePreferences,
        favoriteColors: state.favoriteColors,
        avoidColors: state.avoidColors,
        syncedWithBackend: state.syncedWithBackend,
      }),
    }
  )
);

export default useOnboardingStore;
