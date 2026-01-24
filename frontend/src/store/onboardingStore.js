import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { onboardingApi, faceAnalysisApi, profileApi, parseApiError } from '../api';

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
          
          if (!data.success) {
            throw new Error(data.message || 'Analysis failed');
          }
          
          // Extract analysis results
          const { skin_features, facial_features, color_recommendations, style_tips } = data;
          
          // Transform to expected format
          const faceAnalysis = {
            skinTone: skin_features?.skin_depth || 'Medium',
            skinToneHex: skin_features?.skin_hex || '#D4A574',
            undertone: skin_features?.undertone || 'warm',
            seasonalType: skin_features?.seasonal_type || 'autumn',
            faceShape: facial_features?.face_shape || 'oval',
            confidence: skin_features?.confidence || 0.8,
            // Raw data for API calls
            lab_l: skin_features?.lab_l,
            lab_a: skin_features?.lab_a,
            lab_b: skin_features?.lab_b,
            skin_rgb: skin_features?.skin_rgb,
          };
          
          set({
            faceAnalysis,
            skinFeatures: skin_features,
            facialFeatures: facial_features,
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
          return { success: false, error: 'User not authenticated' };
        }
        
        set({ isSaving: true, error: null });
        
        try {
          const onboardingData = get().getOnboardingData();
          
          // Submit skin tone if we have face analysis
          if (onboardingData.faceAnalysis?.undertone) {
            try {
              await onboardingApi.submitSkinTone(userId, {
                skin_tone: onboardingData.faceAnalysis.undertone,
              });
            } catch (e) {
              console.log('Skin tone sync optional');
            }
          }
          
          // Submit body type
          if (onboardingData.bodyType) {
            try {
              await onboardingApi.submitBodyType(userId, {
                body_type: onboardingData.bodyType,
              });
            } catch (e) {
              console.log('Body type sync optional');
            }
          }
          
          // Submit style preferences
          if (onboardingData.stylePreferences?.length) {
            try {
              await onboardingApi.submitStyle(userId, {
                style_preference: onboardingData.stylePreferences[0],
                color_preferences: onboardingData.favoriteColors,
              });
            } catch (e) {
              console.log('Style sync optional');
            }
          }
          
          // Complete onboarding
          try {
            await onboardingApi.complete(userId);
          } catch (e) {
            console.log('Complete endpoint optional');
          }
          
          // Update profile with all data
          try {
            await profileApi.updateProfile(userId, {
              body_type: onboardingData.bodyType,
              skin_tone: onboardingData.faceAnalysis?.undertone,
              style_preference: onboardingData.stylePreferences?.[0],
              height: onboardingData.height,
              onboarding_complete: true,
            });
          } catch (e) {
            console.log('Profile update optional');
          }
          
          set({ isSaving: false, syncedWithBackend: true });
          return { success: true };
        } catch (error) {
          const { message } = parseApiError(error);
          set({ error: message, isSaving: false });
          return { success: false, error: message };
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

      // Check if onboarding is complete
      isComplete: () => {
        const { authCompleted, faceAnalysis, bodyType, stylePreferences } = get();
        return (
          authCompleted &&
          faceAnalysis !== null &&
          bodyType !== null &&
          stylePreferences.length > 0
        );
      },

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
