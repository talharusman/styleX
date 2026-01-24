import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight } from 'lucide-react';
import { useOnboardingStore } from '../../../store';
import { userApi } from '../../../api';
import Button from '../../../components/ui/Button';
import styles from './StepComplete.module.css';

const StepComplete = () => {
  const navigate = useNavigate();
  const { getOnboardingData, resetOnboarding } = useOnboardingStore();

  const handleComplete = async () => {
    try {
      // Save onboarding data to backend
      const data = getOnboardingData();
      await userApi.updateProfile({
        ...data,
        onboardingCompleted: true,
      });

      // Reset onboarding store and navigate to dashboard
      resetOnboarding();
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to save profile:', error);
      // Still navigate to dashboard on error - data is saved locally
      navigate('/dashboard');
    }
  };

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

      <motion.div
        className={styles.actions}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <Button
          size="lg"
          onClick={handleComplete}
          icon={<ArrowRight size={20} />}
          iconPosition="right"
        >
          Start Exploring
        </Button>
      </motion.div>
    </div>
  );
};

export default StepComplete;
