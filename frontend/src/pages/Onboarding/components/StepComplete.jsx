import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, AlertCircle } from 'lucide-react';
import { useOnboardingStore, useAuthStore } from '../../../store';
import Button from '../../../components/ui/Button';
import styles from './StepComplete.module.css';

/**
 * StepComplete Component
 * Final step of onboarding - saves all data to backend and redirects to dashboard
 * 
 * Backend APIs Used:
 * - POST /api/onboarding/step/skin-tone/{userId}
 * - POST /api/onboarding/step/body-type/{userId}
 * - POST /api/onboarding/step/style/{userId}
 * - POST /api/onboarding/step/complete/{userId}
 * - PATCH /api/profile/{userId}
 */
const StepComplete = () => {
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const { updateUser } = useAuthStore();
  const { 
    getOnboardingData, 
    completeOnboarding, 
    resetOnboarding,
    isSaving 
  } = useOnboardingStore();

  const handleComplete = async () => {
    setError(null);

    const result = await completeOnboarding();

    if (!result.success) {
      // Stay on this step: the account is only finished once the server accepts it.
      setError(result.error || 'Something went wrong. Please try again.');
      return;
    }

    updateUser({ onboardingCompleted: true });
    // Clear the locally cached selfie analysis/answers (they are saved on the server now).
    // `completed` is kept, so the route guards let the user into the app.
    resetOnboarding();
    navigate('/dashboard');
  };

  const onboardingData = getOnboardingData();

  return (
    <div className={styles.step}>
      <motion.div
        className={styles.iconWrapper}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 15 }}
      >
        <div className={styles.icon}>
          <Sparkles size={48} />
        </div>
      </motion.div>

      <motion.div
        className={styles.content}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <h2 className={styles.title}>You're All Set!</h2>
        <p className={styles.subtitle}>
          Your style profile is ready. Get ready to discover outfits curated
          just for you.
        </p>
      </motion.div>

      {/* Summary of collected data */}
      {onboardingData && (
        <motion.div
          className={styles.summary}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Body Type:</span>
            <span className={styles.summaryValue} style={{ textTransform: 'capitalize' }}>
              {onboardingData.bodyType || 'Not set'}
            </span>
          </div>
          {onboardingData.faceAnalysis?.undertone && (
            <div className={styles.summaryItem}>
              <span className={styles.summaryLabel}>Undertone:</span>
              <span className={styles.summaryValue} style={{ textTransform: 'capitalize' }}>
                {onboardingData.faceAnalysis.undertone}
              </span>
            </div>
          )}
          {onboardingData.stylePreferences?.length > 0 && (
            <div className={styles.summaryItem}>
              <span className={styles.summaryLabel}>Style:</span>
              <span className={styles.summaryValue}>
                {onboardingData.stylePreferences.slice(0, 3).join(', ')}
              </span>
            </div>
          )}
        </motion.div>
      )}

      <motion.div
        className={styles.highlights}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div className={styles.highlight}>
          <span className={styles.highlightIcon}>✨</span>
          <div className={styles.highlightText}>
            <strong>Personalized Recommendations</strong>
            <span>Outfits matched to your features and style</span>
          </div>
        </div>
        <div className={styles.highlight}>
          <span className={styles.highlightIcon}>📅</span>
          <div className={styles.highlightText}>
            <strong>Event-Based Styling</strong>
            <span>Perfect looks for every occasion</span>
          </div>
        </div>
        <div className={styles.highlight}>
          <span className={styles.highlightIcon}>🌤️</span>
          <div className={styles.highlightText}>
            <strong>Weather-Aware Suggestions</strong>
            <span>Always dressed appropriately</span>
          </div>
        </div>
      </motion.div>

      {error && (
        <motion.div 
          className={styles.error}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <AlertCircle size={16} />
          <span>{error}</span>
        </motion.div>
      )}

      <motion.div
        className={styles.actions}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <Button
          size="lg"
          onClick={handleComplete}
          loading={isSaving}
          icon={<ArrowRight size={20} />}
          iconPosition="right"
        >
          {isSaving ? 'Saving...' : 'Start Exploring'}
        </Button>
      </motion.div>
    </div>
  );
};

export default StepComplete;
