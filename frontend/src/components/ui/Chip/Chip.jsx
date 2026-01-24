import { motion } from 'framer-motion';
import styles from './Chip.module.css';

const Chip = ({
  children,
  variant = 'default',
  size = 'md',
  selected = false,
  icon,
  onRemove,
  onClick,
  className = '',
  ...props
}) => {
  const chipClasses = [
    styles.chip,
    styles[variant],
    styles[size],
    selected && styles.selected,
    onClick && styles.clickable,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <motion.span
      className={chipClasses}
      onClick={onClick}
      whileHover={onClick ? { scale: 1.02 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
      {...props}
    >
      {icon && <span className={styles.icon}>{icon}</span>}
      <span className={styles.label}>{children}</span>
      {onRemove && (
        <button
          className={styles.removeButton}
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          aria-label="Remove"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path
              d="M10.5 3.5L3.5 10.5M3.5 3.5L10.5 10.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        </button>
      )}
    </motion.span>
  );
};

// Chip Group for multi-select
Chip.Group = ({ children, className = '', ...props }) => (
  <div className={`${styles.group} ${className}`} {...props}>
    {children}
  </div>
);

export default Chip;
