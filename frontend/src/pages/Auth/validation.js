const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

/**
 * Client-side validation for the auth form. Mirrors the backend rules
 * (RegisterRequest in backend/app/auth/schemas.py); the server stays authoritative.
 *
 * @param {'login'|'register'} mode
 * @returns {Object} map of field name -> error message (empty when valid)
 */
export function validateAuthForm(mode, { name = '', email = '', password = '', confirm = '' }) {
  const errors = {};

  if (mode === 'register' && name.trim().length < 2) {
    errors.name = 'Enter your name (at least 2 characters)';
  }

  if (!EMAIL_RE.test(email.trim())) {
    errors.email = 'Enter a valid email address';
  }

  if (mode === 'register') {
    if (password.length < 8) {
      errors.password = 'Use at least 8 characters';
    } else if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
      errors.password = 'Include at least one letter and one number';
    }
    if (confirm !== password) {
      errors.confirm = 'Passwords do not match';
    }
  } else if (!password) {
    errors.password = 'Enter your password';
  }

  return errors;
}
