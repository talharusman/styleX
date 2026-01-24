import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Sun,
  Cloud,
  CloudRain,
  Calendar,
  RefreshCw,
  ChevronRight,
  Heart,
  Share2,
  Bookmark,
} from 'lucide-react';
import { useAuthStore, useDashboardStore } from '../../store';
import { Header } from '../../components/layout';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import { staggerContainer, staggerItem } from '../../styles/tokens';
import styles from './Dashboard.module.css';

const Dashboard = () => {
  const { user } = useAuthStore();
  const {
    greeting,
    weather,
    weatherLoading,
    todayEvents,
    eventsLoading,
    recommendations,
    recommendationsLoading,
    activeRecommendationIndex,
    initDashboard,
    regenerateRecommendations,
    nextRecommendation,
    prevRecommendation,
    saveOutfit,
  } = useDashboardStore();

  useEffect(() => {
    // Get user location and initialize dashboard
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          initDashboard(user?.id, {
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          });
        },
        () => {
          // Fallback without location
          initDashboard(user?.id, null);
        }
      );
    } else {
      initDashboard(user?.id, null);
    }
  }, [user?.id, initDashboard]);

  const getWeatherIcon = (condition) => {
    switch (condition?.toLowerCase()) {
      case 'sunny':
      case 'clear':
        return <Sun size={24} />;
      case 'cloudy':
      case 'overcast':
        return <Cloud size={24} />;
      case 'rain':
      case 'rainy':
        return <CloudRain size={24} />;
      default:
        return <Sun size={24} />;
    }
  };

  const activeRecommendation = recommendations[activeRecommendationIndex];

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
          {/* Greeting Section */}
          <motion.section className={styles.greeting} variants={staggerItem}>
            <div className={styles.greetingContent}>
              <span className={styles.greetingTime}>{greeting}</span>
              <h1 className={styles.greetingName}>
                {user?.name?.split(' ')[0] || 'there'}
              </h1>
              <p className={styles.greetingSubtitle}>
                Here's your personalized style for today
              </p>
            </div>

            {/* Weather Widget */}
            {weather && (
              <div className={styles.weatherWidget}>
                <div className={styles.weatherIcon}>
                  {getWeatherIcon(weather.condition)}
                </div>
                <div className={styles.weatherInfo}>
                  <span className={styles.weatherTemp}>{weather.temp || '22'}°C</span>
                  <span className={styles.weatherCondition}>
                    {weather.condition || 'Clear'}
                  </span>
                </div>
              </div>
            )}
          </motion.section>

          {/* Today's Events */}
          <motion.section className={styles.events} variants={staggerItem}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Today's Events</h2>
              <Link to="/calendar" className={styles.sectionLink}>
                View Calendar <ChevronRight size={16} />
              </Link>
            </div>

            {eventsLoading ? (
              <div className={styles.eventsSkeleton}>
                <div className={styles.skeletonCard} />
                <div className={styles.skeletonCard} />
              </div>
            ) : todayEvents.length > 0 ? (
              <div className={styles.eventsList}>
                {todayEvents.slice(0, 3).map((event) => (
                  <Card key={event.id} variant="flat" padding="sm" hoverable>
                    <div className={styles.eventCard}>
                      <div className={styles.eventTime}>
                        <Calendar size={14} />
                        <span>{event.time || '9:00 AM'}</span>
                      </div>
                      <span className={styles.eventTitle}>
                        {event.title || 'Team Meeting'}
                      </span>
                      <span className={styles.eventType}>
                        {event.type || 'Business Casual'}
                      </span>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <div className={styles.eventsEmpty}>
                <Calendar size={32} className={styles.emptyIcon} />
                <p>No events scheduled for today</p>
                <Link to="/calendar">
                  <Button variant="outline" size="sm">
                    Add Event
                  </Button>
                </Link>
              </div>
            )}
          </motion.section>

          {/* Outfit Recommendations */}
          <motion.section className={styles.recommendations} variants={staggerItem}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Today's Outfit</h2>
              <Button
                variant="ghost"
                size="sm"
                icon={<RefreshCw size={16} />}
                onClick={regenerateRecommendations}
                loading={recommendationsLoading}
              >
                Regenerate
              </Button>
            </div>

            {recommendationsLoading ? (
              <div className={styles.outfitSkeleton}>
                <div className={styles.skeletonOutfit} />
              </div>
            ) : activeRecommendation ? (
              <div className={styles.outfitShowcase}>
                {/* Main Outfit Display */}
                <motion.div
                  className={styles.outfitMain}
                  key={activeRecommendationIndex}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className={styles.outfitImage}>
                    <img
                      src={
                        activeRecommendation.image ||
                        'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600&q=80'
                      }
                      alt="Outfit recommendation"
                    />
                  </div>

                  <div className={styles.outfitDetails}>
                    <h3 className={styles.outfitTitle}>
                      {activeRecommendation.title || 'Refined Casual'}
                    </h3>
                    <p className={styles.outfitDescription}>
                      {activeRecommendation.description ||
                        'A sophisticated blend of comfort and style, perfect for a productive day.'}
                    </p>

                    {/* Color Palette */}
                    <div className={styles.colorPalette}>
                      <span className={styles.paletteLabel}>Color Palette</span>
                      <div className={styles.paletteColors}>
                        {(
                          activeRecommendation.colors || [
                            '#2C3E50',
                            '#E6DCCF',
                            '#6B7C5A',
                            '#0E0E0E',
                          ]
                        ).map((color, i) => (
                          <span
                            key={i}
                            className={styles.paletteColor}
                            style={{ backgroundColor: color }}
                            title={color}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Outfit Items */}
                    <div className={styles.outfitItems}>
                      {(
                        activeRecommendation.items || [
                          { category: 'Top', name: 'Linen Button-Up Shirt' },
                          { category: 'Bottom', name: 'Tailored Chinos' },
                          { category: 'Footwear', name: 'Suede Loafers' },
                          { category: 'Accessory', name: 'Leather Belt' },
                        ]
                      ).map((item, i) => (
                        <div key={i} className={styles.outfitItem}>
                          <span className={styles.itemCategory}>{item.category}</span>
                          <span className={styles.itemName}>{item.name}</span>
                        </div>
                      ))}
                    </div>

                    {/* Actions */}
                    <div className={styles.outfitActions}>
                      <Button
                        icon={<Bookmark size={18} />}
                        onClick={() => saveOutfit(activeRecommendation.id)}
                      >
                        Save Outfit
                      </Button>
                      <Button variant="outline" icon={<Share2 size={18} />}>
                        Share
                      </Button>
                      <Link to={`/recommendation/${activeRecommendation.id}`}>
                        <Button variant="ghost">View Details</Button>
                      </Link>
                    </div>
                  </div>
                </motion.div>

                {/* Navigation dots */}
                {recommendations.length > 1 && (
                  <div className={styles.outfitNav}>
                    {recommendations.map((_, i) => (
                      <button
                        key={i}
                        className={`${styles.navDot} ${
                          i === activeRecommendationIndex ? styles.active : ''
                        }`}
                        onClick={() => useDashboardStore.getState().setActiveRecommendation(i)}
                        aria-label={`View outfit ${i + 1}`}
                      />
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className={styles.outfitEmpty}>
                <p>No recommendations yet. Let's generate your first outfit!</p>
                <Button onClick={regenerateRecommendations}>Generate Outfit</Button>
              </div>
            )}
          </motion.section>

          {/* Why This Works */}
          {activeRecommendation && (
            <motion.section className={styles.whySection} variants={staggerItem}>
              <h2 className={styles.sectionTitle}>Why This Works For You</h2>
              <div className={styles.whyGrid}>
                <Card variant="flat" padding="md">
                  <div className={styles.whyCard}>
                    <span className={styles.whyIcon}>🎨</span>
                    <h4>Color Harmony</h4>
                    <p>
                      These colors complement your warm undertone and enhance
                      your natural features.
                    </p>
                  </div>
                </Card>
                <Card variant="flat" padding="md">
                  <div className={styles.whyCard}>
                    <span className={styles.whyIcon}>👔</span>
                    <h4>Style Match</h4>
                    <p>
                      Aligned with your minimal and classic style preferences
                      for a refined look.
                    </p>
                  </div>
                </Card>
                <Card variant="flat" padding="md">
                  <div className={styles.whyCard}>
                    <span className={styles.whyIcon}>🌤️</span>
                    <h4>Weather Ready</h4>
                    <p>
                      Light, breathable fabrics perfect for today's clear
                      weather.
                    </p>
                  </div>
                </Card>
              </div>
            </motion.section>
          )}
        </motion.div>
      </main>
    </div>
  );
};

export default Dashboard;
