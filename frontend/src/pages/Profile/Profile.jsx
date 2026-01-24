import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Camera, Edit2, Save, X, AlertCircle } from 'lucide-react';
import { useAuthStore } from '../../store';
import { profileApi, faceAnalysisApi, parseApiError } from '../../api';
import { Header } from '../../components/layout';
import Button from '../../components/ui/Button';
import Avatar from '../../components/ui/Avatar';
import Card from '../../components/ui/Card';
import Chip from '../../components/ui/Chip';
import { staggerContainer, staggerItem } from '../../styles/tokens';
import styles from './Profile.module.css';

/**
 * Profile Page
 * Displays and allows editing of user profile data
 * 
 * Backend APIs Used:
 * - GET /api/profile/{userId} - Get user profile
 * - PATCH /api/profile/{userId} - Update user profile
 * - GET /api/profile/{userId}/style - Get style profile
 * - GET /api/profile/{userId}/color-recommendations - Get color recommendations
 * - POST /api/face-analysis/analyze/upload - Re-analyze selfie
 */

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
  const userId = user?.user_id || localStorage.getItem('userId');
  
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetchingProfile, setFetchingProfile] = useState(true);
  const [error, setError] = useState(null);
  const [colorRecommendations, setColorRecommendations] = useState(null);
  
  const [profile, setProfile] = useState({
    name: user?.name || '',
    email: user?.email || '',
    bodyType: user?.bodyType || user?.body_type || 'average',
    skinTone: user?.skinTone || user?.skin_tone || 'Medium Warm',
    undertone: user?.undertone || 'Warm',
    stylePreferences: user?.stylePreferences || user?.style_preference ? 
      [user?.style_preference] : ['Minimal', 'Classic'],
    favoriteColors: user?.favoriteColors || ['neutrals'],
    height: user?.height || '',
    gender: user?.gender || '',
  });

  // Fetch full profile from backend on mount
  useEffect(() => {
    const fetchProfile = async () => {
      if (!userId) {
        setFetchingProfile(false);
        return;
      }
      
      try {
        const response = await profileApi.getProfile(userId);
        const data = response.data;
        
        setProfile({
          name: data.name || profile.name,
          email: data.email || profile.email,
          bodyType: data.body_type || profile.bodyType,
          skinTone: data.skin_tone || profile.skinTone,
          undertone: data.undertone || profile.undertone,
          stylePreferences: data.style_preference ? 
            (Array.isArray(data.style_preference) ? data.style_preference : [data.style_preference]) : 
            profile.stylePreferences,
          favoriteColors: data.favorite_colors || profile.favoriteColors,
          height: data.height || profile.height,
          gender: data.gender || profile.gender,
        });
        
        // Also fetch color recommendations
        try {
          const colorResponse = await profileApi.getColorRecommendations(userId);
          setColorRecommendations(colorResponse.data);
        } catch (e) {
          // Color recommendations endpoint may not be available
        }
      } catch (error) {
        console.error('Failed to fetch profile:', error);
        // Use local data
      } finally {
        setFetchingProfile(false);
      }
    };
    
    fetchProfile();
  }, [userId]);

  /**
   * Save profile changes to backend
   * PATCH /api/profile/{userId}
   */
  const handleSave = async () => {
    if (!userId) {
      setError('User not authenticated');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await profileApi.updateProfile(userId, {
        name: profile.name,
        body_type: profile.bodyType,
        skin_tone: profile.skinTone,
        style_preference: profile.stylePreferences[0], // API expects single value
        height: profile.height,
        gender: profile.gender,
      });
      
      // Update local auth store
      updateUser({
        ...profile,
        body_type: profile.bodyType,
        skin_tone: profile.skinTone,
        style_preference: profile.stylePreferences[0],
      });
      
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update profile:', error);
      const { message } = parseApiError(error);
      setError(message || 'Failed to save changes. Please try again.');
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

  /**
   * Re-analyze selfie for updated skin/undertone
   * Would trigger POST /api/face-analysis/analyze/upload
   */
  const handleRetakeSelfie = () => {
    // This would open a modal or navigate to selfie capture
    // For now, we'll just log
    console.log('Retake selfie analysis');
    // In production: navigate to /onboarding with step=2 or open modal
  };

  if (fetchingProfile) {
    return (
      <div className={styles.page}>
        <Header />
        <main className={styles.main}>
          <div className={styles.loading}>Loading profile...</div>
        </main>
      </div>
    );
  }

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
              onClick={() => {
                if (isEditing) {
                  // Cancel - reset to original values
                  setError(null);
                }
                setIsEditing(!isEditing);
              }}
            >
              {isEditing ? 'Cancel' : 'Edit Profile'}
            </Button>
          </motion.section>

          {/* Error message */}
          {error && (
            <motion.div className={styles.errorBanner} variants={staggerItem}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </motion.div>
          )}

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
                    <Button variant="outline" size="sm" onClick={handleRetakeSelfie}>
                      Retake Selfie Analysis
                    </Button>
                  </div>
                )}
              </Card>
            </motion.section>

            {/* Color Recommendations from API */}
            {colorRecommendations && (
              <motion.section variants={staggerItem}>
                <Card padding="lg">
                  <h2 className={styles.sectionTitle}>Your Best Colors</h2>
                  <p className={styles.sectionDescription}>
                    Based on your skin tone analysis, these colors will look great on you.
                  </p>
                  
                  <div className={styles.colorRecsGrid}>
                    {colorRecommendations.best_colors?.slice(0, 6).map((color, i) => (
                      <span key={i} className={styles.colorRecTag}>
                        {color}
                      </span>
                    ))}
                  </div>
                  
                  {colorRecommendations.avoid_colors?.length > 0 && (
                    <>
                      <h3 className={styles.subSectionTitle}>Colors to Avoid</h3>
                      <div className={styles.colorRecsGrid}>
                        {colorRecommendations.avoid_colors?.slice(0, 4).map((color, i) => (
                          <span key={i} className={styles.colorAvoidTag}>
                            {color}
                          </span>
                        ))}
                      </div>
                    </>
                  )}
                </Card>
              </motion.section>
            )}

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
