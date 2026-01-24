import { forwardRef } from 'react';
import styles from './Input.module.css';

const Input = forwardRef(
  (
    {
      label,
      error,
      hint,
      icon,
      iconPosition = 'left',
      variant = 'default',
      size = 'md',
      fullWidth = true,
      className = '',
      type = 'text',
      ...props
    },
    ref
  ) => {
    const wrapperClasses = [
      styles.wrapper,
      fullWidth && styles.fullWidth,
      className,
    ]
      .filter(Boolean)
      .join(' ');

    const inputWrapperClasses = [
      styles.inputWrapper,
      styles[variant],
      styles[size],
      error && styles.error,
      icon && styles[`icon-${iconPosition}`],
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div className={wrapperClasses}>
        {label && (
          <label className={styles.label}>
            {label}
          </label>
        )}
        <div className={inputWrapperClasses}>
          {icon && iconPosition === 'left' && (
            <span className={styles.icon}>{icon}</span>
          )}
          <input
            ref={ref}
            type={type}
            className={styles.input}
            {...props}
          />
          {icon && iconPosition === 'right' && (
            <span className={styles.icon}>{icon}</span>
          )}
        </div>
        {(error || hint) && (
          <span className={error ? styles.errorText : styles.hint}>
            {error || hint}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
