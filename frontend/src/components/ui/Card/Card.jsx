import { motion } from 'framer-motion';
import styles from './Card.module.css';

const Card = ({
  children,
  variant = 'default',
  padding = 'md',
  hoverable = false,
  clickable = false,
  className = '',
  onClick,
  ...props
}) => {
  const cardClasses = [
    styles.card,
    styles[variant],
    styles[`padding-${padding}`],
    hoverable && styles.hoverable,
    clickable && styles.clickable,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <motion.div
      className={cardClasses}
      onClick={clickable ? onClick : undefined}
      whileHover={hoverable ? { y: -4 } : undefined}
      transition={{ duration: 0.2 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

// Card subcomponents
Card.Header = ({ children, className = '', ...props }) => (
  <div className={`${styles.header} ${className}`} {...props}>
    {children}
  </div>
);

Card.Body = ({ children, className = '', ...props }) => (
  <div className={`${styles.body} ${className}`} {...props}>
    {children}
  </div>
);

Card.Footer = ({ children, className = '', ...props }) => (
  <div className={`${styles.footer} ${className}`} {...props}>
    {children}
  </div>
);

Card.Image = ({ src, alt, aspectRatio = '4/3', className = '', ...props }) => (
  <div
    className={`${styles.imageWrapper} ${className}`}
    style={{ aspectRatio }}
    {...props}
  >
    <img src={src} alt={alt} className={styles.image} />
  </div>
);

export default Card;
