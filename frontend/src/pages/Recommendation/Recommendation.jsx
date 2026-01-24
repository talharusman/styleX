import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Heart,
  Share2,
  Bookmark,
  BookmarkCheck,
  RefreshCw,
  ExternalLink,
  Check,
} from 'lucide-react';
import { recommendationApi } from '../../api';
import { Header } from '../../components/layout';
import Button from '../../components/ui/Button';
import Card from '../../components/ui/Card';
import { staggerContainer, staggerItem } from '../../styles/tokens';
import styles from './Recommendation.module.css';

const Recommendation = () => {
  const { id } = useParams();
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isSaved, setIsSaved] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  useEffect(() => {
    const fetchRecommendation = async () => {
      try {
        setLoading(true);
        const response = await recommendationApi.getById(id);
        setRecommendation(response.data);
        setIsSaved(response.data.isSaved);
      } catch (error) {
        console.error('Failed to fetch recommendation:', error);
        // Use mock data for demo
        setRecommendation({
          id,
          title: 'Modern Professional',
          description:
            'A sophisticated ensemble that balances professionalism with contemporary style. Perfect for important meetings or client presentations.',
          image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&q=80',
          colors: ['#2C3E50', '#E6DCCF', '#6B7C5A', '#0E0E0E'],
          items: [
            {
              category: 'Top',
              name: 'Navy Merino Wool Sweater',
              brand: 'Everlane',
              price: '$98',
              image: 'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=400&q=80',
            },
            {
              category: 'Bottom',
              name: 'Tailored Wool Trousers',
              brand: 'Theory',
              price: '$275',
              image: 'https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400&q=80',
            },
            {
              category: 'Footwear',
              name: 'Leather Oxford Shoes',
              brand: 'Cole Haan',
              price: '$180',
              image: 'https://images.unsplash.com/photo-1449505278894-297fdb3edbc1?w=400&q=80',
            },
            {
              category: 'Accessory',
              name: 'Leather Belt',
              brand: 'Fossil',
              price: '$45',
              image: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&q=80',
            },
          ],
          styleNotes: [
            'The navy sweater complements your cool undertone beautifully',
            'Tailored fit enhances your athletic build',
            'Neutral palette aligns with your minimal style preference',
            'Layerable pieces work well for fluctuating office temperatures',
          ],
          occasion: 'Business Casual',
          weather: 'Indoor / Mild',
        });
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendation();
  }, [id]);

  const handleSave = async () => {
    try {
      if (isSaved) {
        await recommendationApi.unsaveOutfit(id);
      } else {
        await recommendationApi.saveOutfit(id);
      }
      setIsSaved(!isSaved);
    } catch (error) {
      console.error('Failed to save outfit:', error);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: recommendation.title,
          text: recommendation.description,
          url: window.location.href,
        });
      } catch (error) {
        console.log('Share cancelled');
      }
    } else {
      navigator.clipboard.writeText(window.location.href);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      const response = await recommendationApi.generate({ regenerate: true });
      setRecommendation(response.data);
    } catch (error) {
      console.error('Failed to regenerate:', error);
    } finally {
      setRegenerating(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <Header />
        <main className={styles.main}>
          <div className={styles.loading}>
            <div className={styles.loadingSpinner} />
            <p>Loading recommendation...</p>
          </div>
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
          {/* Back Navigation */}
          <motion.div variants={staggerItem}>
            <Link to="/dashboard" className={styles.backLink}>
              <ArrowLeft size={18} />
              <span>Back to Dashboard</span>
            </Link>
          </motion.div>

          {/* Main Content */}
          <div className={styles.content}>
            {/* Outfit Image */}
            <motion.div className={styles.imageSection} variants={staggerItem}>
              <div className={styles.mainImage}>
                <img src={recommendation.image} alt={recommendation.title} />
              </div>

              {/* Color Palette */}
              <div className={styles.colorPalette}>
                <h3 className={styles.sectionLabel}>Color Palette</h3>
                <div className={styles.colors}>
                  {recommendation.colors.map((color, i) => (
                    <div key={i} className={styles.colorItem}>
                      <span
                        className={styles.colorSwatch}
                        style={{ backgroundColor: color }}
                      />
                      <span className={styles.colorCode}>{color}</span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>

            {/* Outfit Details */}
            <motion.div className={styles.detailsSection} variants={staggerItem}>
              {/* Header */}
              <div className={styles.header}>
                <div className={styles.headerInfo}>
                  <span className={styles.occasion}>{recommendation.occasion}</span>
                  <h1 className={styles.title}>{recommendation.title}</h1>
                  <p className={styles.description}>{recommendation.description}</p>
                </div>

                {/* Actions */}
                <div className={styles.actions}>
                  <Button
                    variant={isSaved ? 'accent' : 'outline'}
                    icon={isSaved ? <BookmarkCheck size={18} /> : <Bookmark size={18} />}
                    onClick={handleSave}
                  >
                    {isSaved ? 'Saved' : 'Save'}
                  </Button>
                  <Button variant="outline" icon={<Share2 size={18} />} onClick={handleShare}>
                    Share
                  </Button>
                  <Button
                    variant="ghost"
                    icon={<RefreshCw size={18} />}
                    onClick={handleRegenerate}
                    loading={regenerating}
                  >
                    Regenerate
                  </Button>
                </div>
              </div>

              {/* Outfit Items */}
              <div className={styles.items}>
                <h3 className={styles.sectionLabel}>Outfit Breakdown</h3>
                <div className={styles.itemsGrid}>
                  {recommendation.items.map((item, i) => (
                    <motion.div
                      key={i}
                      className={styles.itemCard}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.1 * i }}
                    >
                      <div className={styles.itemImage}>
                        <img src={item.image} alt={item.name} />
                      </div>
                      <div className={styles.itemInfo}>
                        <span className={styles.itemCategory}>{item.category}</span>
                        <h4 className={styles.itemName}>{item.name}</h4>
                        <div className={styles.itemMeta}>
                          <span className={styles.itemBrand}>{item.brand}</span>
                          <span className={styles.itemPrice}>{item.price}</span>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Style Notes */}
              <div className={styles.styleNotes}>
                <h3 className={styles.sectionLabel}>Why This Works For You</h3>
                <ul className={styles.notesList}>
                  {recommendation.styleNotes.map((note, i) => (
                    <motion.li
                      key={i}
                      className={styles.note}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.1 * i }}
                    >
                      <Check size={16} className={styles.noteIcon} />
                      <span>{note}</span>
                    </motion.li>
                  ))}
                </ul>
              </div>

              {/* Weather / Occasion Tags */}
              <div className={styles.tags}>
                <span className={styles.tag}>{recommendation.occasion}</span>
                <span className={styles.tag}>{recommendation.weather}</span>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </main>
    </div>
  );
};

export default Recommendation;
