import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Button } from '../../ui';
import styles from './Header.module.css';

const Header = ({ variant = 'default', showAuth = true }) => {
  const location = useLocation();
  const isLanding = location.pathname === '/';

  return (
    <motion.header
      className={`${styles.header} ${styles[variant]}`}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div className={styles.container}>
        {/* Logo */}
        <Link to="/" className={styles.logo}>
          <span className={styles.logoText}>inStyle</span>
        </Link>

        {/* Navigation */}
        <nav className={styles.nav}>
          {!isLanding && (
            <>
              <Link to="/dashboard" className={styles.navLink}>
                Dashboard
              </Link>
              <Link to="/calendar" className={styles.navLink}>
                Calendar
              </Link>
              <Link to="/profile" className={styles.navLink}>
                Profile
              </Link>
            </>
          )}
        </nav>

        {/* Actions */}
        <div className={styles.actions}>
          {showAuth && isLanding && (
            <>
              <Button variant="ghost" to="/auth">
                Sign In
              </Button>
              <Button variant="primary" to="/auth">
                Get Started
              </Button>
            </>
          )}
        </div>
      </div>
    </motion.header>
  );
};

export default Header;
