import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Camera, Edit2, Save, X } from 'lucide-react';
import { useAuthStore } from '../../store';
import { userApi } from '../../api';
import { Header } from '../../components/layout';
import Button from '../../components/ui/Button';
import Avatar from '../../components/ui/Avatar';
import Card from '../../components/ui/Card';
import Chip from '../../components/ui/Chip';
import { staggerContainer, staggerItem } from '../../styles/tokens';
import styles from './Profile.module.css';

const styleOptions = [
  'Minimal', 'Classic', 'Streetwear', 'Bohemian', 'Athletic',
  'Preppy', 'Edgy', 'Smart Casual', 'Vintage', 'Glamorous'
];

const colorPalettes = [
  { id: 'neutrals', label: 'Neutrals', colors: ['#0E0E0E', '#5A5A5A', '#E6DCCF'] },
  { id: 'earth', label: 'Earth Tones', colors: ['#8B4513', '#6B7C5A', '#D4A574'] },
  { id: 'pastels', label: 'Pastels', colors: ['#FFB6C1', '#B0E0E6', '#98FB98'] },
  { id: 'bold', label: 'Bold', colors: ['#FF0000', '#0000FF', '#FFFF00'] },
];

const Profile = () => {
  const { user, updateUser } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState({
    name: user?.name || '',
    email: user?.email || '',
    bodyType: user?.bodyType || 'average',
    skinTone: user?.skinTone || 'Medium Warm',
    undertone: user?.undertone || 'Warm',
    stylePreferences: user?.stylePreferences || ['Minimal', 'Classic'],
    favoriteColors: user?.favoriteColors || ['neutrals'],
    height: user?.height || '',
  });

  const handleSave = async () => {
    setLoading(true);
    try {
      await userApi.updateProfile(profile);
      updateUser(profile);
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleStyle = (style) => {
    setProfile((prev) => ({
      ...prev,
      stylePreferences: prev.stylePreferences.includes(style)
        ? prev.stylePreferences.filter((s) => s !== style)
        : [...prev.stylePreferences, style],
    }));
  };

  const toggleColorPalette = (paletteId) => {
    setProfile((prev) => ({
      ...prev,
      favoriteColors: prev.favoriteColors.includes(paletteId)
        ? prev.favoriteColors.filter((c) => c !== paletteId)
        : [...prev.favoriteColors, paletteId],
    }));
  };

  return (
    <div className={styles.page}>
      <Header />

      <main className={styles.main}>
        <motion.div
          className={styles.container}
          initial="initial"
          animate="animate"
          variants={staggerContainer}
        >
          {/* Profile Header */}
          <motion.section className={styles.header} variants={staggerItem}>
            <div className={styles.avatarSection}>
              <div className={styles.avatarWrapper}>
                <Avatar
                  src={user?.avatar}
                  name={profile.name}
                  size="xxl"
                />
                <button className={styles.avatarEdit}>
                  <Camera size={16} />
                </button>
              </div>
              <div className={styles.userInfo}>
                <h1 className={styles.userName}>{profile.name}</h1>
                <p className={styles.userEmail}>{profile.email}</p>
              </div>
            </div>

            <Button
              variant={isEditing ? 'outline' : 'primary'}
              icon={isEditing ? <X size={18} /> : <Edit2 size={18} />}
              onClick={() => setIsEditing(!isEditing)}
            >
              {isEditing ? 'Cancel' : 'Edit Profile'}
            </Button>
          </motion.section>

          {/* Profile Content */}
          <div className={styles.content}>
            {/* Physical Attributes */}
            <motion.section variants={staggerItem}>
              <Card padding="lg">
                <h2 className={styles.sectionTitle}>Physical Attributes</h2>
                <p className={styles.sectionDescription}>
                  These attributes help us recommend colors and styles that complement you.
                </p>

                <div className={styles.attributesGrid}>
                  <div className={styles.attribute}>
                    <span className={styles.attributeLabel}>Skin Tone</span>
                    <div className={styles.attributeValue}>
                      <span
                        className={styles.colorIndicator}
                        style={{ backgroundColor: '#D4A574' }}
                      />
                      {profile.skinTone}
                    </div>
                  </div>

                  <div className={styles.attribute}>
                    <span className={styles.attributeLabel}>Undertone</span>
                    <span className={styles.attributeValue}>{profile.undertone}</span>
                  </div>

                  <div className={styles.attribute}>
                    <span className={styles.attributeLabel}>Body Type</span>
                    <span className={styles.attributeValue} style={{ textTransform: 'capitalize' }}>
                      {profile.bodyType}
                    </span>
                  </div>

                  <div className={styles.attribute}>
                    <span className={styles.attributeLabel}>Height</span>
                    <span className={styles.attributeValue}>
                      {profile.height || 'Not set'}
                    </span>
                  </div>
                </div>

                {isEditing && (
                  <div className={styles.editSection}>
                    <Button variant="outline" size="sm">
                      Retake Selfie Analysis
                    </Button>
                  </div>
                )}
              </Card>
            </motion.section>

            {/* Style Preferences */}
            <motion.section variants={staggerItem}>
              <Card padding="lg">
                <h2 className={styles.sectionTitle}>Style Preferences</h2>
                <p className={styles.sectionDescription}>
                  Select the style aesthetics that resonate with you.
                </p>

                <div className={styles.chipGrid}>
                  {styleOptions.map((style) => (
                    <Chip
                      key={style}
                      selected={profile.stylePreferences.includes(style)}
                      onClick={isEditing ? () => toggleStyle(style) : undefined}
                      className={!isEditing ? styles.chipDisabled : ''}
                    >
                      {style}
                    </Chip>
                  ))}
                </div>
              </Card>
            </motion.section>

            {/* Color Preferences */}
            <motion.section variants={staggerItem}>
              <Card padding="lg">
                <h2 className={styles.sectionTitle}>Favorite Color Palettes</h2>
                <p className={styles.sectionDescription}>
                  We'll prioritize these color families in your recommendations.
                </p>

                <div className={styles.paletteGrid}>
                  {colorPalettes.map((palette) => (
                    <button
                      key={palette.id}
                      className={`${styles.paletteCard} ${
                        profile.favoriteColors.includes(palette.id) ? styles.selected : ''
                      } ${!isEditing ? styles.disabled : ''}`}
                      onClick={isEditing ? () => toggleColorPalette(palette.id) : undefined}
                    >
                      <div className={styles.paletteColors}>
                        {palette.colors.map((color, i) => (
                          <span
                            key={i}
                            className={styles.paletteSwatch}
                            style={{ backgroundColor: color }}
                          />
                        ))}
                      </div>
                      <span className={styles.paletteLabel}>{palette.label}</span>
                    </button>
                  ))}
                </div>
              </Card>
            </motion.section>

            {/* Stats */}
            <motion.section variants={staggerItem}>
              <Card padding="lg">
                <h2 className={styles.sectionTitle}>Your Style Journey</h2>

                <div className={styles.statsGrid}>
                  <div className={styles.stat}>
                    <span className={styles.statValue}>47</span>
                    <span className={styles.statLabel}>Outfits Generated</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statValue}>12</span>
                    <span className={styles.statLabel}>Saved Looks</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statValue}>8</span>
                    <span className={styles.statLabel}>Events Styled</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statValue}>23</span>
                    <span className={styles.statLabel}>Days Active</span>
                  </div>
                </div>
              </Card>
            </motion.section>
          </div>

          {/* Save Button */}
          {isEditing && (
            <motion.div
              className={styles.saveBar}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <p>You have unsaved changes</p>
              <Button icon={<Save size={18} />} onClick={handleSave} loading={loading}>
                Save Changes
              </Button>
            </motion.div>
          )}
        </motion.div>
      </main>
    </div>
  );
};

export default Profile;
