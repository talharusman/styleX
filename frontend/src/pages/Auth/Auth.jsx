import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuthStore } from '../../store';
import Button from '../../components/ui/Button';
import { fadeInUp, staggerContainer, staggerItem } from '../../styles/tokens';
import styles from './Auth.module.css';

const Auth = () => {
  const navigate = useNavigate();
  const { login, isLoading, error } = useAuthStore();
  const [authError, setAuthError] = useState(null);

  const handleGoogleSignIn = async () => {
    setAuthError(null);
    
    // In production, this would use Firebase Google Auth
    // For demo, we'll simulate the flow
    try {
      // Simulate getting Google token
      const mockGoogleToken = 'mock_google_token_' + Date.now();
      
      const result = await login(mockGoogleToken);
      
      if (result.success) {
        // Check if user needs onboarding
        if (!result.user?.onboardingCompleted) {
          navigate('/onboarding');
        } else {
          navigate('/dashboard');
        }
      } else {
        setAuthError(result.error);
      }
    } catch (err) {
      setAuthError('Failed to sign in. Please try again.');
    }
  };

  return (
    <div className={styles.page}>
      {/* Left Panel - Branding */}
      <motion.div
        className={styles.brandPanel}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className={styles.brandContent}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <span className={styles.logo}>inStyle</span>
          </motion.div>
          
          <motion.h1
            className={styles.brandTitle}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            Your personal
            <br />
            style journey
            <br />
            starts here.
          </motion.h1>

          <motion.p
            className={styles.brandSubtitle}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            Join thousands discovering their perfect look with AI-powered styling.
          </motion.p>
        </div>

        {/* Background image */}
        <div className={styles.brandImage}>
          <img
            src="https://images.unsplash.com/photo-1558171813-4c088753af8f?w=1200&q=80"
            alt=""
            aria-hidden="true"
          />
        </div>
      </motion.div>

      {/* Right Panel - Auth Form */}
      <motion.div
        className={styles.authPanel}
        initial="initial"
        animate="animate"
        variants={staggerContainer}
      >
        <div className={styles.authContent}>
          <motion.div className={styles.authHeader} variants={staggerItem}>
            <h2 className={styles.authTitle}>Welcome</h2>
            <p className={styles.authSubtitle}>
              Sign in to continue to inStyle
            </p>
          </motion.div>

          <motion.div className={styles.authForm} variants={staggerItem}>
            {(error || authError) && (
              <div className={styles.errorMessage}>
                {error || authError}
              </div>
            )}

            <Button
              variant="outline"
              size="lg"
              fullWidth
              onClick={handleGoogleSignIn}
              loading={isLoading}
              icon={
                <svg viewBox="0 0 24 24" width="20" height="20">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
              }
            >
              Continue with Google
            </Button>

            <div className={styles.divider}>
              <span>Secure sign-in powered by Google</span>
            </div>
          </motion.div>

          <motion.div className={styles.authFooter} variants={staggerItem}>
            <p className={styles.termsText}>
              By continuing, you agree to our{' '}
              <a href="/terms" className={styles.link}>Terms of Service</a>
              {' '}and{' '}
              <a href="/privacy" className={styles.link}>Privacy Policy</a>
            </p>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};

export default Auth;
