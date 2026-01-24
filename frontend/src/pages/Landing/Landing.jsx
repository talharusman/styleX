import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, Calendar, Palette, Sun } from 'lucide-react';
import { Header, Footer } from '../../components/layout';
import Button from '../../components/ui/Button';
import { fadeInUp, staggerContainer, staggerItem } from '../../styles/tokens';
import styles from './Landing.module.css';

const Landing = () => {
  const features = [
    {
      icon: <Sparkles size={24} />,
      title: 'AI-Powered Styling',
      description:
        'Our intelligent system analyzes your unique features to create perfectly matched outfits.',
    },
    {
      icon: <Palette size={24} />,
      title: 'Color Harmony',
      description:
        'Recommendations based on your skin tone and undertone for colors that make you glow.',
    },
    {
      icon: <Calendar size={24} />,
      title: 'Event-Ready',
      description:
        'From casual brunch to formal events, get outfit suggestions for every occasion.',
    },
    {
      icon: <Sun size={24} />,
      title: 'Weather-Aware',
      description:
        'Real-time weather integration ensures you are always dressed for the conditions.',
    },
  ];

  const testimonials = [
    {
      quote: "Finally, an app that understands my style. It is like having a personal stylist in my pocket.",
      author: 'Sarah M.',
      role: 'Fashion Blogger',
    },
    {
      quote: 'The color recommendations were spot-on. I have received more compliments in a month than all last year.',
      author: 'James K.',
      role: 'Creative Director',
    },
    {
      quote: 'Perfect for my busy schedule. I spend less time deciding what to wear and more time being productive.',
      author: 'Emily R.',
      role: 'Entrepreneur',
    },
  ];

  return (
    <div className={styles.page}>
      <Header variant="transparent" />

      {/* Hero Section */}
      <section className={styles.hero}>
        <div className={styles.heroBackground}>
          <div className={styles.heroGradient} />
        </div>

        <motion.div
          className={styles.heroContent}
          initial="initial"
          animate="animate"
          variants={staggerContainer}
        >
          <motion.span className={styles.heroBadge} variants={staggerItem}>
            AI-Powered Personal Styling
          </motion.span>

          <motion.h1 className={styles.heroTitle} variants={staggerItem}>
            Dress with
            <br />
            <span className={styles.heroTitleAccent}>Confidence</span>
          </motion.h1>

          <motion.p className={styles.heroSubtitle} variants={staggerItem}>
            Your personal AI stylist that understands your body, your style,
            and your schedule. Get outfit recommendations that make you look
            and feel exceptional.
          </motion.p>

          <motion.div className={styles.heroActions} variants={staggerItem}>
            <Button
              to="/auth"
              size="lg"
              icon={<ArrowRight size={20} />}
              iconPosition="right"
            >
              Get Styled Free
            </Button>
            <Button href="#features" variant="outline" size="lg">
              See How It Works
            </Button>
          </motion.div>

          <motion.div className={styles.heroStats} variants={staggerItem}>
            <div className={styles.stat}>
              <span className={styles.statValue}>50K+</span>
              <span className={styles.statLabel}>Happy Users</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.stat}>
              <span className={styles.statValue}>1M+</span>
              <span className={styles.statLabel}>Outfits Created</span>
            </div>
            <div className={styles.statDivider} />
            <div className={styles.stat}>
              <span className={styles.statValue}>4.9★</span>
              <span className={styles.statLabel}>User Rating</span>
            </div>
          </motion.div>
        </motion.div>

        {/* Hero Image */}
        <motion.div
          className={styles.heroImageWrapper}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        >
          <div className={styles.heroImageGrid}>
            <div className={styles.heroImageMain}>
              <img
                src="https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600&q=80"
                alt="Fashion editorial"
                className={styles.heroImage}
              />
            </div>
            <div className={styles.heroImageSecondary}>
              <img
                src="https://images.unsplash.com/photo-1558171813-4c088753af8f?w=400&q=80"
                alt="Style details"
                className={styles.heroImage}
              />
            </div>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section id="features" className={styles.features}>
        <div className={styles.container}>
          <motion.div
            className={styles.sectionHeader}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className={styles.sectionLabel}>Features</span>
            <h2 className={styles.sectionTitle}>
              Style Intelligence,
              <br />
              Simplified
            </h2>
            <p className={styles.sectionSubtitle}>
              Powered by advanced AI that understands fashion, color theory,
              and your unique attributes.
            </p>
          </motion.div>

          <motion.div
            className={styles.featureGrid}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={staggerContainer}
          >
            {features.map((feature, index) => (
              <motion.div
                key={index}
                className={styles.featureCard}
                variants={fadeInUp}
                whileHover={{ y: -8 }}
                transition={{ duration: 0.3 }}
              >
                <div className={styles.featureIcon}>{feature.icon}</div>
                <h3 className={styles.featureTitle}>{feature.title}</h3>
                <p className={styles.featureDescription}>
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className={styles.howItWorks}>
        <div className={styles.container}>
          <motion.div
            className={styles.sectionHeader}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className={styles.sectionLabel}>How It Works</span>
            <h2 className={styles.sectionTitle}>
              Three Steps to
              <br />
              Perfect Style
            </h2>
          </motion.div>

          <div className={styles.stepsGrid}>
            <motion.div
              className={styles.step}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
            >
              <span className={styles.stepNumber}>01</span>
              <h3 className={styles.stepTitle}>Quick Analysis</h3>
              <p className={styles.stepDescription}>
                Upload a selfie and let our AI analyze your skin tone, undertone,
                and facial features to create your unique style profile.
              </p>
            </motion.div>

            <motion.div
              className={styles.step}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <span className={styles.stepNumber}>02</span>
              <h3 className={styles.stepTitle}>Set Preferences</h3>
              <p className={styles.stepDescription}>
                Tell us your style preferences, body type, and the occasions
                you dress for. The more we know, the better we style.
              </p>
            </motion.div>

            <motion.div
              className={styles.step}
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <span className={styles.stepNumber}>03</span>
              <h3 className={styles.stepTitle}>Get Styled</h3>
              <p className={styles.stepDescription}>
                Receive personalized outfit recommendations daily, for events,
                or on-demand. Save favorites and build your style library.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className={styles.testimonials}>
        <div className={styles.container}>
          <motion.div
            className={styles.sectionHeader}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className={styles.sectionLabel}>Testimonials</span>
            <h2 className={styles.sectionTitle}>
              Loved by Style
              <br />
              Enthusiasts
            </h2>
          </motion.div>

          <motion.div
            className={styles.testimonialGrid}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            variants={staggerContainer}
          >
            {testimonials.map((testimonial, index) => (
              <motion.div
                key={index}
                className={styles.testimonialCard}
                variants={fadeInUp}
              >
                <p className={styles.testimonialQuote}>
                  "{testimonial.quote}"
                </p>
                <div className={styles.testimonialAuthor}>
                  <span className={styles.authorName}>{testimonial.author}</span>
                  <span className={styles.authorRole}>{testimonial.role}</span>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className={styles.cta}>
        <div className={styles.container}>
          <motion.div
            className={styles.ctaContent}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className={styles.ctaTitle}>
              Ready to Transform
              <br />
              Your Style?
            </h2>
            <p className={styles.ctaSubtitle}>
              Join thousands who've discovered their perfect look with inStyle.
            </p>
            <Button
              to="/auth"
              size="xl"
              icon={<ArrowRight size={20} />}
              iconPosition="right"
            >
              Start Your Style Journey
            </Button>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Landing;
