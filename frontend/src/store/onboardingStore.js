import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useOnboardingStore = create(
  persist(
    (set, get) => ({
      // Current step (1-5)
      currentStep: 1,
      totalSteps: 5,
      
      // Step 1: Auth completed
      authCompleted: false,
      
      // Step 2: Selfie data
      selfieData: null,
      faceAnalysis: null,
      
      // Step 3: Body type
      bodyType: null,
      height: null,
      
      // Step 4: Style preferences
      stylePreferences: [],
      favoriteColors: [],
      avoidColors: [],
      
      // Loading states
      isAnalyzing: false,
      error: null,

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

      // Step 2: Selfie
      setSelfieData: (data, analysis) => {
        set({
          selfieData: data,
          faceAnalysis: analysis,
          isAnalyzing: false,
        });
      },

      setAnalyzing: (isAnalyzing) => set({ isAnalyzing }),

      // Step 3: Body type
      setBodyType: (bodyType) => set({ bodyType }),
      setHeight: (height) => set({ height }),

      // Step 4: Style preferences
      setStylePreferences: (preferences) => set({ stylePreferences: preferences }),
      
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

      // Reset onboarding
      resetOnboarding: () => {
        set({
          currentStep: 1,
          authCompleted: false,
          selfieData: null,
          faceAnalysis: null,
          bodyType: null,
          height: null,
          stylePreferences: [],
          favoriteColors: [],
          avoidColors: [],
          isAnalyzing: false,
          error: null,
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
          bodyType,
          height,
          stylePreferences,
          favoriteColors,
          avoidColors,
        } = get();

        return {
          faceAnalysis,
          bodyType,
          height,
          stylePreferences,
          favoriteColors,
          avoidColors,
        };
      },
    }),
    {
      name: 'onboarding-storage',
      partialize: (state) => ({
        currentStep: state.currentStep,
        authCompleted: state.authCompleted,
        faceAnalysis: state.faceAnalysis,
        bodyType: state.bodyType,
        height: state.height,
        stylePreferences: state.stylePreferences,
        favoriteColors: state.favoriteColors,
        avoidColors: state.avoidColors,
      }),
    }
  )
);

export default useOnboardingStore;
