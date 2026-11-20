import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Eye, EyeOff } from 'lucide-react';
import { useAuthStore, useOnboardingStore } from '../../store';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import { staggerContainer, staggerItem } from '../../styles/tokens';
import { validateAuthForm } from './validation';
import styles from './Auth.module.css';

const Auth = () => {
  const navigate = useNavigate();
  const { loginWithEmail, register, isLoading, error, clearError } = useAuthStore();
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' });
  const [fieldErrors, setFieldErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);

  const isRegister = mode === 'register';

  const update = (field) => (e) => {
    setForm((f) => ({ ...f, [field]: e.target.value }));
    if (fieldErrors[field]) setFieldErrors((fe) => ({ ...fe, [field]: undefined }));
  };

  const switchMode = () => {
    setMode(isRegister ? 'login' : 'register');
    setFieldErrors({});
    setShowPassword(false);
    clearError();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = validateAuthForm(mode, form);
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    const email = form.email.trim();
    const result = isRegister
      ? await register(email, form.password, form.name.trim())
      : await loginWithEmail(email, form.password);

    if (result.success) {
      const complete = useOnboardingStore.getState().isComplete();
      navigate(complete ? '/dashboard' : '/onboarding', { replace: true });
    }
  };

  return (
    <div className={styles.page}>
      {/* Left Panel - Branding */}
      <motion.div
        className={styles.brandPanel}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className={styles.brandContent}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <span className={styles.logo}>inStyle</span>
          </motion.div>

          <motion.h1
            className={styles.brandTitle}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
          >
            Your personal
            <br />
            style journey
            <br />
            starts here.
          </motion.h1>

          <motion.p
            className={styles.brandSubtitle}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            Discover your perfect look with AI-powered styling.
          </motion.p>
        </div>

        {/* Background image */}
        <div className={styles.brandImage}>
          <img
            src="https://images.unsplash.com/photo-1558171813-4c088753af8f?w=1200&q=80"
            alt=""
            aria-hidden="true"
          />
        </div>
      </motion.div>

      {/* Right Panel - Auth Form */}
      <motion.div
        className={styles.authPanel}
        initial="initial"
        animate="animate"
        variants={staggerContainer}
      >
        <div className={styles.authContent}>
          <motion.div className={styles.authHeader} variants={staggerItem}>
            <h2 className={styles.authTitle}>
              {isRegister ? 'Create your account' : 'Welcome back'}
            </h2>
            <p className={styles.authSubtitle}>
              {isRegister
                ? 'Start your personal style journey'
                : 'Sign in to continue to inStyle'}
            </p>
          </motion.div>

          <motion.form
            className={styles.authForm}
            variants={staggerItem}
            onSubmit={handleSubmit}
            noValidate
          >
            {error && (
              <div className={styles.errorMessage} role="alert">
                {error}
              </div>
            )}

            {isRegister && (
              <Input
                label="Name"
                aria-label="Name"
                type="text"
                autoComplete="name"
                value={form.name}
                onChange={update('name')}
                error={fieldErrors.name}
                placeholder="Your name"
              />
            )}

            <Input
              label="Email"
              aria-label="Email"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={update('email')}
              error={fieldErrors.email}
              placeholder="you@example.com"
            />

            <div className={styles.passwordField}>
              <Input
                label="Password"
                aria-label="Password"
                type={showPassword ? 'text' : 'password'}
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                value={form.password}
                onChange={update('password')}
                error={fieldErrors.password}
                hint={isRegister ? 'At least 8 characters, with a letter and a number' : undefined}
                placeholder="Password"
              />
              <button
                type="button"
                className={styles.toggleVisibility}
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                aria-pressed={showPassword}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            {isRegister && (
              <Input
                label="Confirm password"
                aria-label="Confirm password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={form.confirm}
                onChange={update('confirm')}
                error={fieldErrors.confirm}
                placeholder="Repeat password"
              />
            )}

            <Button type="submit" variant="primary" size="lg" fullWidth loading={isLoading}>
              {isRegister ? 'Create account' : 'Sign in'}
            </Button>

            <p className={styles.switchMode}>
              {isRegister ? 'Already have an account?' : 'No account yet?'}{' '}
              <button type="button" className={styles.linkButton} onClick={switchMode}>
                {isRegister ? 'Sign in' : 'Create account'}
              </button>
            </p>
          </motion.form>

          <motion.div className={styles.authFooter} variants={staggerItem}>
            <p className={styles.termsText}>
              By continuing, you agree to our{' '}
              <a href="/terms" className={styles.link}>Terms of Service</a>
              {' '}and{' '}
              <a href="/privacy" className={styles.link}>Privacy Policy</a>
            </p>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};

export default Auth;
