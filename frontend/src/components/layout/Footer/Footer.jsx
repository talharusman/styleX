import { Link } from 'react-router-dom';
import { Instagram, Twitter } from 'lucide-react';
import styles from './Footer.module.css';

const Footer = () => {
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.grid}>
          {/* Brand */}
          <div className={styles.brand}>
            <Link to="/" className={styles.logo}>
              <span className={styles.logoText}>inStyle</span>
            </Link>
            <p className={styles.tagline}>
              Your personal AI-powered fashion stylist. Look confident, feel exceptional.
            </p>
            <div className={styles.social}>
              <a href="#" aria-label="Instagram" className={styles.socialLink}>
                <Instagram size={20} />
              </a>
              <a href="#" aria-label="Twitter" className={styles.socialLink}>
                <Twitter size={20} />
              </a>
            </div>
          </div>

          {/* Links */}
          <div className={styles.links}>
            <div className={styles.linkGroup}>
              <h4 className={styles.linkTitle}>Product</h4>
              <Link to="/" className={styles.link}>Features</Link>
              <Link to="/" className={styles.link}>How it Works</Link>
              <Link to="/" className={styles.link}>Pricing</Link>
            </div>

            <div className={styles.linkGroup}>
              <h4 className={styles.linkTitle}>Company</h4>
              <Link to="/" className={styles.link}>About</Link>
              <Link to="/" className={styles.link}>Blog</Link>
              <Link to="/" className={styles.link}>Careers</Link>
            </div>

            <div className={styles.linkGroup}>
              <h4 className={styles.linkTitle}>Legal</h4>
              <Link to="/" className={styles.link}>Privacy</Link>
              <Link to="/" className={styles.link}>Terms</Link>
              <Link to="/" className={styles.link}>Cookies</Link>
            </div>
          </div>
        </div>

        <div className={styles.bottom}>
          <p className={styles.copyright}>
            © {new Date().getFullYear()} inStyle. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
