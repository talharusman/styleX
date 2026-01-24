import styles from './Avatar.module.css';

const Avatar = ({
  src,
  alt = '',
  name = '',
  size = 'md',
  variant = 'circle',
  status,
  className = '',
  ...props
}) => {
  const getInitials = (name) => {
    if (!name) return '';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const avatarClasses = [
    styles.avatar,
    styles[size],
    styles[variant],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={avatarClasses} {...props}>
      {src ? (
        <img src={src} alt={alt || name} className={styles.image} />
      ) : (
        <span className={styles.initials}>{getInitials(name)}</span>
      )}
      {status && (
        <span className={`${styles.status} ${styles[`status-${status}`]}`} />
      )}
    </div>
  );
};

export default Avatar;
