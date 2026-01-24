import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore, useOnboardingStore } from './store';
import {
  Landing,
  Auth,
  Onboarding,
  Dashboard,
  Recommendation,
  Calendar,
  Profile,
  Settings,
} from './pages';
import './styles/global.css';

// Protected Route wrapper
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  
  return children;
}

// Onboarding Guard - ensures users complete onboarding
function OnboardingGuard({ children }) {
  const { isAuthenticated } = useAuthStore();
  const { isComplete } = useOnboardingStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  
  if (!isComplete) {
    return <Navigate to="/onboarding" replace />;
  }
  
  return children;
}

// Auth Route - redirects authenticated users
function AuthRoute({ children }) {
  const { isAuthenticated } = useAuthStore();
  const { isComplete } = useOnboardingStore();
  
  if (isAuthenticated && isComplete) {
    return <Navigate to="/dashboard" replace />;
  }
  
  if (isAuthenticated && !isComplete) {
    return <Navigate to="/onboarding" replace />;
  }
  
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Landing />} />
        
        <Route
          path="/auth"
          element={
            <AuthRoute>
              <Auth />
            </AuthRoute>
          }
        />
        
        {/* Onboarding - requires auth but not completion */}
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <Onboarding />
            </ProtectedRoute>
          }
        />
        
        {/* Protected Routes - require auth and completed onboarding */}
        <Route
          path="/dashboard"
          element={
            <OnboardingGuard>
              <Dashboard />
            </OnboardingGuard>
          }
        />
        
        <Route
          path="/recommendation/:id"
          element={
            <OnboardingGuard>
              <Recommendation />
            </OnboardingGuard>
          }
        />
        
        <Route
          path="/calendar"
          element={
            <OnboardingGuard>
              <Calendar />
            </OnboardingGuard>
          }
        />
        
        <Route
          path="/profile"
          element={
            <OnboardingGuard>
              <Profile />
            </OnboardingGuard>
          }
        />
        
        <Route
          path="/settings"
          element={
            <OnboardingGuard>
              <Settings />
            </OnboardingGuard>
          }
        />
        
        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
