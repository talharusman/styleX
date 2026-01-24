import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import { useOnboardingStore } from '../../../store';
import Button from '../../../components/ui/Button';
import styles from './StepBodyType.module.css';

const bodyTypes = [
  {
    id: 'lean',
    label: 'Lean',
    description: 'Slim build with narrow shoulders',
    icon: '🏃',
  },
  {
    id: 'average',
    label: 'Average',
    description: 'Balanced proportions',
    icon: '🧍',
  },
  {
    id: 'athletic',
    label: 'Athletic',
    description: 'Muscular with broad shoulders',
    icon: '💪',
  },
  {
    id: 'bulky',
    label: 'Bulky',
    description: 'Larger build with wide frame',
    icon: '🏋️',
  },
];

const StepBodyType = () => {
  const { bodyType, setBodyType, nextStep, prevStep } = useOnboardingStore();

  const handleSelect = (type) => {
    setBodyType(type);
  };

  return (
    <div className={styles.step}>
      <div className={styles.header}>
        <h2 className={styles.title}>Select Your Body Type</h2>
        <p className={styles.subtitle}>
          This helps us recommend clothes that fit and flatter your frame.
        </p>
      </div>

      <div className={styles.body}>
        <div className={styles.optionsGrid}>
          {bodyTypes.map((type) => (
            <motion.button
              key={type.id}
              className={`${styles.option} ${
                bodyType === type.id ? styles.selected : ''
              }`}
              onClick={() => handleSelect(type.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <span className={styles.optionIcon}>{type.icon}</span>
              <span className={styles.optionLabel}>{type.label}</span>
              <span className={styles.optionDescription}>{type.description}</span>
            </motion.button>
          ))}
        </div>
      </div>

      <div className={styles.actions}>
        <Button variant="ghost" onClick={prevStep} icon={<ArrowLeft size={18} />}>
          Back
        </Button>
        <Button onClick={nextStep} disabled={!bodyType}>
          Continue
        </Button>
      </div>
    </div>
  );
};

export default StepBodyType;
