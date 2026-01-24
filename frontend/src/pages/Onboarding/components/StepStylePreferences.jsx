import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import { useOnboardingStore } from '../../../store';
import Button from '../../../components/ui/Button';
import Chip from '../../../components/ui/Chip';
import styles from './StepStylePreferences.module.css';

const styleOptions = [
  { id: 'minimal', label: 'Minimal', emoji: '⬜' },
  { id: 'classic', label: 'Classic', emoji: '👔' },
  { id: 'streetwear', label: 'Streetwear', emoji: '🧢' },
  { id: 'bohemian', label: 'Bohemian', emoji: '🌸' },
  { id: 'athletic', label: 'Athletic', emoji: '🏃' },
  { id: 'preppy', label: 'Preppy', emoji: '🎓' },
  { id: 'edgy', label: 'Edgy', emoji: '🖤' },
  { id: 'smart-casual', label: 'Smart Casual', emoji: '✨' },
  { id: 'vintage', label: 'Vintage', emoji: '📻' },
  { id: 'glamorous', label: 'Glamorous', emoji: '💎' },
];

const colorOptions = [
  { id: 'neutrals', label: 'Neutrals', colors: ['#0E0E0E', '#5A5A5A', '#E6DCCF', '#FFFFFF'] },
  { id: 'earth-tones', label: 'Earth Tones', colors: ['#8B4513', '#6B7C5A', '#D4A574', '#C9A227'] },
  { id: 'pastels', label: 'Pastels', colors: ['#FFB6C1', '#B0E0E6', '#98FB98', '#DDA0DD'] },
  { id: 'bold', label: 'Bold Colors', colors: ['#FF0000', '#0000FF', '#FFFF00', '#FF00FF'] },
  { id: 'monochrome', label: 'Monochrome', colors: ['#000000', '#404040', '#808080', '#FFFFFF'] },
];

const StepStylePreferences = () => {
  const {
    stylePreferences,
    toggleStylePreference,
    favoriteColors,
    setFavoriteColors,
    nextStep,
    prevStep,
  } = useOnboardingStore();

  const toggleColor = (colorId) => {
    if (favoriteColors.includes(colorId)) {
      setFavoriteColors(favoriteColors.filter((c) => c !== colorId));
    } else {
      setFavoriteColors([...favoriteColors, colorId]);
    }
  };

  const canContinue = stylePreferences.length >= 2;

  return (
    <div className={styles.step}>
      <div className={styles.header}>
        <h2 className={styles.title}>Define Your Style</h2>
        <p className={styles.subtitle}>
          Select at least 2 style aesthetics that resonate with you.
        </p>
      </div>

      <div className={styles.body}>
        {/* Style Preferences */}
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Style Aesthetics</h3>
          <div className={styles.styleGrid}>
            {styleOptions.map((style) => (
              <motion.button
                key={style.id}
                className={`${styles.styleCard} ${
                  stylePreferences.includes(style.id) ? styles.selected : ''
                }`}
                onClick={() => toggleStylePreference(style.id)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <span className={styles.styleEmoji}>{style.emoji}</span>
                <span className={styles.styleLabel}>{style.label}</span>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Color Preferences */}
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Color Palettes You Love</h3>
          <div className={styles.colorGrid}>
            {colorOptions.map((palette) => (
              <motion.button
                key={palette.id}
                className={`${styles.colorCard} ${
                  favoriteColors.includes(palette.id) ? styles.selected : ''
                }`}
                onClick={() => toggleColor(palette.id)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className={styles.colorSwatches}>
                  {palette.colors.map((color, i) => (
                    <span
                      key={i}
                      className={styles.swatch}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
                <span className={styles.colorLabel}>{palette.label}</span>
              </motion.button>
            ))}
          </div>
        </div>
      </div>

      <div className={styles.actions}>
        <Button variant="ghost" onClick={prevStep} icon={<ArrowLeft size={18} />}>
          Back
        </Button>
        <Button onClick={nextStep} disabled={!canContinue}>
          {canContinue ? 'Continue' : `Select ${2 - stylePreferences.length} more`}
        </Button>
      </div>
    </div>
  );
};

export default StepStylePreferences;
