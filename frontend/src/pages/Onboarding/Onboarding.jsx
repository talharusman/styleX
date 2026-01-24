import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useOnboardingStore, useAuthStore } from '../../store';
import StepIndicator from './components/StepIndicator';
import StepSelfie from './components/StepSelfie';
import StepBodyType from './components/StepBodyType';
import StepStylePreferences from './components/StepStylePreferences';
import StepComplete from './components/StepComplete';
import styles from './Onboarding.module.css';

const Onboarding = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const { currentStep, totalSteps } = useOnboardingStore();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/auth');
    }
  }, [isAuthenticated, navigate]);

  const renderStep = () => {
    switch (currentStep) {
      case 1:
      case 2:
        return <StepSelfie />;
      case 3:
        return <StepBodyType />;
      case 4:
        return <StepStylePreferences />;
      case 5:
        return <StepComplete />;
      default:
        return <StepSelfie />;
    }
  };

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <span className={styles.logo}>inStyle</span>
        <StepIndicator current={currentStep} total={totalSteps} />
        <div className={styles.headerSpacer} />
      </header>

      {/* Main content */}
      <main className={styles.main}>
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className={styles.stepContainer}
          >
            {renderStep()}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
};

export default Onboarding;
