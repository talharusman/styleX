import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User,
  Bell,
  Shield,
  Palette,
  HelpCircle,
  LogOut,
  ChevronRight,
  Moon,
  Sun,
  Smartphone,
  Mail,
  Calendar,
  Trash2,
  Download,
  ExternalLink,
  Check,
  X,
  AlertTriangle,
} from 'lucide-react';
import { useAuthStore } from '../../store';
import { Button, Card, Modal } from '../../components/ui';
import { Header, Footer } from '../../components/layout';
import styles from './Settings.module.css';

const settingsSections = [
  {
    id: 'account',
    title: 'Account',
    icon: User,
    description: 'Manage your account details and preferences',
  },
  {
    id: 'notifications',
    title: 'Notifications',
    icon: Bell,
    description: 'Control how and when we reach you',
  },
  {
    id: 'privacy',
    title: 'Privacy & Security',
    icon: Shield,
    description: 'Manage your data and security settings',
  },
  {
    id: 'appearance',
    title: 'Appearance',
    icon: Palette,
    description: 'Customize how inStyle looks',
  },
  {
    id: 'help',
    title: 'Help & Support',
    icon: HelpCircle,
    description: 'Get help and contact support',
  },
];

function Settings() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [activeSection, setActiveSection] = useState('account');
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  
  // Settings state
  const [settings, setSettings] = useState({
    // Notifications
    emailNotifications: true,
    pushNotifications: true,
    weeklyDigest: true,
    eventReminders: true,
    styleUpdates: false,
    
    // Appearance
    theme: 'system', // 'light', 'dark', 'system'
    compactMode: false,
    
    // Privacy
    profileVisibility: 'private',
    dataSharing: false,
    analytics: true,
  });

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const handleDeleteAccount = async () => {
    // In production, this would call an API
    console.log('Deleting account...');
    await logout();
    navigate('/');
  };

  const renderSection = () => {
    switch (activeSection) {
      case 'account':
        return <AccountSection user={user} />;
      case 'notifications':
        return (
          <NotificationsSection
            settings={settings}
            onChange={handleSettingChange}
          />
        );
      case 'privacy':
        return (
          <PrivacySection
            settings={settings}
            onChange={handleSettingChange}
            onDeleteAccount={() => setShowDeleteModal(true)}
          />
        );
      case 'appearance':
        return (
          <AppearanceSection
            settings={settings}
            onChange={handleSettingChange}
          />
        );
      case 'help':
        return <HelpSection />;
      default:
        return null;
    }
  };

  return (
    <div className={styles.page}>
      <Header />
      
      <main className={styles.main}>
        <div className={styles.container}>
          <motion.div
            className={styles.header}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className={styles.title}>Settings</h1>
            <p className={styles.subtitle}>
              Manage your account and preferences
            </p>
          </motion.div>

          <div className={styles.content}>
            {/* Sidebar Navigation */}
            <motion.nav
              className={styles.sidebar}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <div className={styles.sidebarSections}>
                {settingsSections.map((section) => {
                  const Icon = section.icon;
                  const isActive = activeSection === section.id;
                  
                  return (
                    <button
                      key={section.id}
                      className={`${styles.sidebarItem} ${isActive ? styles.active : ''}`}
                      onClick={() => setActiveSection(section.id)}
                    >
                      <Icon size={20} />
                      <div className={styles.sidebarItemText}>
                        <span className={styles.sidebarItemTitle}>
                          {section.title}
                        </span>
                        <span className={styles.sidebarItemDesc}>
                          {section.description}
                        </span>
                      </div>
                      <ChevronRight size={16} className={styles.chevron} />
                    </button>
                  );
                })}
              </div>

              <button
                className={styles.logoutButton}
                onClick={() => setShowLogoutModal(true)}
              >
                <LogOut size={20} />
                <span>Log Out</span>
              </button>
            </motion.nav>

            {/* Settings Content */}
            <motion.div
              className={styles.settingsContent}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeSection}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                >
                  {renderSection()}
                </motion.div>
              </AnimatePresence>
            </motion.div>
          </div>
        </div>
      </main>

      <Footer />

      {/* Logout Modal */}
      <Modal
        isOpen={showLogoutModal}
        onClose={() => setShowLogoutModal(false)}
        title="Log Out"
        size="small"
      >
        <div className={styles.modalContent}>
          <p>Are you sure you want to log out of your account?</p>
          <div className={styles.modalActions}>
            <Button
              variant="ghost"
              onClick={() => setShowLogoutModal(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleLogout}>
              Log Out
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Account Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Delete Account"
        size="small"
      >
        <div className={styles.modalContent}>
          <div className={styles.deleteWarning}>
            <AlertTriangle size={48} />
            <p>
              This action is <strong>permanent</strong> and cannot be undone.
              All your data, preferences, and history will be deleted.
            </p>
          </div>
          <div className={styles.modalActions}>
            <Button
              variant="ghost"
              onClick={() => setShowDeleteModal(false)}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              className={styles.deleteButton}
              onClick={handleDeleteAccount}
            >
              Delete My Account
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function AccountSection({ user }) {
  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Account</h2>
      
      <Card className={styles.card}>
        <h3 className={styles.cardTitle}>Profile Information</h3>
        
        <div className={styles.infoGrid}>
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>Name</span>
            <span className={styles.infoValue}>{user?.name || 'Not set'}</span>
          </div>
          <div className={styles.infoItem}>
            <span className={styles.infoLabel}>Email</span>
            <span className={styles.infoValue}>{user?.email || 'Not set'}</span>
          </div>
        </div>

        <Button variant="secondary" size="small">
          Edit Profile
        </Button>
      </Card>

      <Card className={styles.card}>
        <h3 className={styles.cardTitle}>Connected Accounts</h3>
        
        <div className={styles.connectedAccount}>
          <div className={styles.accountInfo}>
            <div className={styles.accountIcon}>
              <svg viewBox="0 0 24 24" width="24" height="24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
            </div>
            <div>
              <p className={styles.accountName}>Google</p>
              <p className={styles.accountEmail}>{user?.email}</p>
            </div>
          </div>
          <span className={styles.connectedBadge}>
            <Check size={14} />
            Connected
          </span>
        </div>
      </Card>

      <Card className={styles.card}>
        <h3 className={styles.cardTitle}>Data Export</h3>
        <p className={styles.cardDescription}>
          Download a copy of all your data including preferences, saved outfits,
          and calendar events.
        </p>
        <Button variant="secondary" size="small">
          <Download size={16} />
          Export Data
        </Button>
      </Card>
    </div>
  );
}

function NotificationsSection({ settings, onChange }) {
  const toggles = [
    {
      key: 'emailNotifications',
      icon: Mail,
      title: 'Email Notifications',
      description: 'Receive updates and recommendations via email',
    },
    {
      key: 'pushNotifications',
      icon: Smartphone,
      title: 'Push Notifications',
      description: 'Get notified on your device',
    },
    {
      key: 'weeklyDigest',
      icon: Mail,
      title: 'Weekly Style Digest',
      description: 'A curated summary of your style recommendations',
    },
    {
      key: 'eventReminders',
      icon: Calendar,
      title: 'Event Reminders',
      description: 'Get reminded about upcoming events and outfit suggestions',
    },
    {
      key: 'styleUpdates',
      icon: Bell,
      title: 'New Features & Updates',
      description: 'Be the first to know about new features',
    },
  ];

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Notifications</h2>
      
      <Card className={styles.card}>
        <div className={styles.toggleList}>
          {toggles.map((toggle) => {
            const Icon = toggle.icon;
            return (
              <div key={toggle.key} className={styles.toggleItem}>
                <div className={styles.toggleInfo}>
                  <Icon size={20} className={styles.toggleIcon} />
                  <div>
                    <p className={styles.toggleTitle}>{toggle.title}</p>
                    <p className={styles.toggleDescription}>
                      {toggle.description}
                    </p>
                  </div>
                </div>
                <button
                  className={`${styles.toggle} ${settings[toggle.key] ? styles.on : ''}`}
                  onClick={() => onChange(toggle.key, !settings[toggle.key])}
                  aria-label={`Toggle ${toggle.title}`}
                >
                  <span className={styles.toggleKnob} />
                </button>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

function PrivacySection({ settings, onChange, onDeleteAccount }) {
  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Privacy & Security</h2>
      
      <Card className={styles.card}>
        <h3 className={styles.cardTitle}>Profile Visibility</h3>
        <p className={styles.cardDescription}>
          Control who can see your profile and style preferences
        </p>
        
        <div className={styles.radioGroup}>
          {['private', 'friends', 'public'].map((option) => (
            <label key={option} className={styles.radioLabel}>
              <input
                type="radio"
                name="visibility"
                value={option}
                checked={settings.profileVisibility === option}
                onChange={() => onChange('profileVisibility', option)}
                className={styles.radioInput}
              />
              <span className={styles.radioCustom} />
              <span className={styles.radioText}>
                {option.charAt(0).toUpperCase() + option.slice(1)}
              </span>
            </label>
          ))}
        </div>
      </Card>

      <Card className={styles.card}>
        <div className={styles.toggleList}>
          <div className={styles.toggleItem}>
            <div className={styles.toggleInfo}>
              <Shield size={20} className={styles.toggleIcon} />
              <div>
                <p className={styles.toggleTitle}>Data Sharing</p>
                <p className={styles.toggleDescription}>
                  Share anonymized data to help improve our recommendations
                </p>
              </div>
            </div>
            <button
              className={`${styles.toggle} ${settings.dataSharing ? styles.on : ''}`}
              onClick={() => onChange('dataSharing', !settings.dataSharing)}
            >
              <span className={styles.toggleKnob} />
            </button>
          </div>
          
          <div className={styles.toggleItem}>
            <div className={styles.toggleInfo}>
              <Shield size={20} className={styles.toggleIcon} />
              <div>
                <p className={styles.toggleTitle}>Analytics</p>
                <p className={styles.toggleDescription}>
                  Help us understand how you use inStyle
                </p>
              </div>
            </div>
            <button
              className={`${styles.toggle} ${settings.analytics ? styles.on : ''}`}
              onClick={() => onChange('analytics', !settings.analytics)}
            >
              <span className={styles.toggleKnob} />
            </button>
          </div>
        </div>
      </Card>

      <Card className={`${styles.card} ${styles.dangerCard}`}>
        <h3 className={styles.cardTitle}>Danger Zone</h3>
        <p className={styles.cardDescription}>
          Permanently delete your account and all associated data.
          This action cannot be undone.
        </p>
        <Button
          variant="ghost"
          className={styles.dangerButton}
          onClick={onDeleteAccount}
        >
          <Trash2 size={16} />
          Delete Account
        </Button>
      </Card>
    </div>
  );
}

function AppearanceSection({ settings, onChange }) {
  const themes = [
    { id: 'light', icon: Sun, label: 'Light' },
    { id: 'dark', icon: Moon, label: 'Dark' },
    { id: 'system', icon: Smartphone, label: 'System' },
  ];

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Appearance</h2>
      
      <Card className={styles.card}>
        <h3 className={styles.cardTitle}>Theme</h3>
        <p className={styles.cardDescription}>
          Choose how inStyle looks to you
        </p>
        
        <div className={styles.themeOptions}>
          {themes.map((theme) => {
            const Icon = theme.icon;
            const isActive = settings.theme === theme.id;
            
            return (
              <button
                key={theme.id}
                className={`${styles.themeOption} ${isActive ? styles.active : ''}`}
                onClick={() => onChange('theme', theme.id)}
              >
                <Icon size={24} />
                <span>{theme.label}</span>
                {isActive && <Check size={16} className={styles.checkIcon} />}
              </button>
            );
          })}
        </div>
      </Card>

      <Card className={styles.card}>
        <div className={styles.toggleList}>
          <div className={styles.toggleItem}>
            <div className={styles.toggleInfo}>
              <Palette size={20} className={styles.toggleIcon} />
              <div>
                <p className={styles.toggleTitle}>Compact Mode</p>
                <p className={styles.toggleDescription}>
                  Reduce spacing and show more content
                </p>
              </div>
            </div>
            <button
              className={`${styles.toggle} ${settings.compactMode ? styles.on : ''}`}
              onClick={() => onChange('compactMode', !settings.compactMode)}
            >
              <span className={styles.toggleKnob} />
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
}

function HelpSection() {
  const helpLinks = [
    {
      title: 'Help Center',
      description: 'Browse our FAQ and guides',
      url: '#',
    },
    {
      title: 'Contact Support',
      description: 'Get help from our team',
      url: '#',
    },
    {
      title: 'Privacy Policy',
      description: 'How we handle your data',
      url: '#',
    },
    {
      title: 'Terms of Service',
      description: 'Our terms and conditions',
      url: '#',
    },
  ];

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Help & Support</h2>
      
      <Card className={styles.card}>
        <div className={styles.helpLinks}>
          {helpLinks.map((link, index) => (
            <a
              key={index}
              href={link.url}
              className={styles.helpLink}
              target="_blank"
              rel="noopener noreferrer"
            >
              <div>
                <p className={styles.helpLinkTitle}>{link.title}</p>
                <p className={styles.helpLinkDescription}>{link.description}</p>
              </div>
              <ExternalLink size={16} />
            </a>
          ))}
        </div>
      </Card>

      <Card className={styles.card}>
        <h3 className={styles.cardTitle}>About inStyle</h3>
        <div className={styles.aboutInfo}>
          <p>Version 1.0.0</p>
          <p>© 2025 inStyle. All rights reserved.</p>
        </div>
      </Card>
    </div>
  );
}

export default Settings;
