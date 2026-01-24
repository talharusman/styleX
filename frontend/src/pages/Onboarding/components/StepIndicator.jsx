import styles from './StepIndicator.module.css';

const StepIndicator = ({ current, total }) => {
  return (
    <div className={styles.indicator}>
      {Array.from({ length: total }, (_, i) => i + 1).map((step) => (
        <div
          key={step}
          className={`${styles.step} ${
            step === current ? styles.active : ''
          } ${step < current ? styles.completed : ''}`}
        >
          <div className={styles.dot} />
          {step < total && <div className={styles.line} />}
        </div>
      ))}
    </div>
  );
};

export default StepIndicator;
