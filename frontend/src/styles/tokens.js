// Design System Tokens for JavaScript/React
// Use these constants for programmatic styling

export const colors = {
  // Primary
  primary: '#0E0E0E',
  primaryLight: '#1A1A1A',
  primaryDark: '#000000',
  
  // Secondary
  secondary: '#E6DCCF',
  secondaryLight: '#F0E8DD',
  secondaryDark: '#D4C7B5',
  
  // Accent
  accent: '#6B7C5A',
  accentLight: '#8A9A76',
  accentDark: '#4D5A40',
  accentAlt: '#B87333', // Burnt Copper
  
  // Background
  bgPrimary: '#FAFAF8',
  bgSecondary: '#F5F4F2',
  bgTertiary: '#EDECEA',
  bgCard: '#FFFFFF',
  bgOverlay: 'rgba(14, 14, 14, 0.5)',
  
  // Text
  textPrimary: '#0E0E0E',
  textSecondary: '#5A5A5A',
  textTertiary: '#8A8A8A',
  textInverse: '#FFFFFF',
  textMuted: '#B0B0B0',
  
  // State
  success: '#4A7C59',
  warning: '#C9A227',
  error: '#B85450',
  info: '#5A7C9A',
  
  // Border
  borderLight: '#E8E6E3',
  borderMedium: '#D4D2CF',
  borderDark: '#B0AEA8',
};

export const fonts = {
  heading: "'Playfair Display', 'Georgia', serif",
  body: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  accent: "'Manrope', 'Inter', sans-serif",
};

export const spacing = {
  0: '0',
  1: '0.25rem',
  2: '0.5rem',
  3: '0.75rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  8: '2rem',
  10: '2.5rem',
  12: '3rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
  32: '8rem',
};

export const radii = {
  none: '0',
  sm: '0.25rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1rem',
  '2xl': '1.5rem',
  '3xl': '2rem',
  full: '9999px',
};

export const shadows = {
  xs: '0 1px 2px rgba(14, 14, 14, 0.04)',
  sm: '0 2px 4px rgba(14, 14, 14, 0.06)',
  md: '0 4px 12px rgba(14, 14, 14, 0.08)',
  lg: '0 8px 24px rgba(14, 14, 14, 0.1)',
  xl: '0 16px 48px rgba(14, 14, 14, 0.12)',
  '2xl': '0 24px 64px rgba(14, 14, 14, 0.16)',
};

export const transitions = {
  fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  normal: '250ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: '400ms cubic-bezier(0.4, 0, 0.2, 1)',
  slower: '600ms cubic-bezier(0.4, 0, 0.2, 1)',
};

// Framer Motion Animation Variants
export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

export const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 20 },
};

export const fadeInDown = {
  initial: { opacity: 0, y: -20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

export const scaleIn = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
};

export const slideInRight = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20 },
};

export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export const staggerItem = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
};
