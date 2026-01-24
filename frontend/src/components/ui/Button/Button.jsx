import { forwardRef } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import styles from './Button.module.css';

// Create motion-enabled Link component
const MotionLink = motion.create(Link);

const Button = forwardRef(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      disabled = false,
      icon,
      iconPosition = 'left',
      as = 'button',
      to,
      href,
      className = '',
      ...props
    },
    ref
  ) => {
    // Determine the component to render
    let Component;
    if (to) {
      // Use react-router Link for internal navigation
      Component = MotionLink;
    } else if (href || as === 'a') {
      // Use anchor for external links
      Component = motion.a;
    } else if (typeof as === 'function' || typeof as === 'object') {
      // Custom component passed (like Link)
      Component = motion.create ? motion.create(as) : motion(as);
    } else {
      // Default to button
      Component = motion.button;
    }

    const buttonClasses = [
      styles.button,
      styles[variant],
      styles[size],
      fullWidth && styles.fullWidth,
      loading && styles.loading,
      disabled && styles.disabled,
      icon && !children && styles.iconOnly,
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <Component
        ref={ref}
        className={buttonClasses}
        disabled={disabled || loading}
        whileHover={{ scale: disabled ? 1 : 1.02 }}
        whileTap={{ scale: disabled ? 1 : 0.98 }}
        transition={{ duration: 0.15 }}
        {...(to ? { to } : {})}
        {...(href ? { href } : {})}
        {...props}
      >
        {loading && (
          <span className={styles.spinner}>
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeDasharray="31.416"
                strokeDashoffset="10"
              />
            </svg>
          </span>
        )}
        {icon && iconPosition === 'left' && !loading && (
          <span className={styles.icon}>{icon}</span>
        )}
        {children && <span className={styles.label}>{children}</span>}
        {icon && iconPosition === 'right' && !loading && (
          <span className={styles.icon}>{icon}</span>
        )}
      </Component>
    );
  }
);

Button.displayName = 'Button';

export default Button;
