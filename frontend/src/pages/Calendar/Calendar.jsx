import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronLeft,
  ChevronRight,
  Plus,
  Calendar as CalendarIcon,
  Clock,
  MapPin,
  X,
  Shirt,
} from 'lucide-react';
import {
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  addDays,
  addMonths,
  subMonths,
  isSameMonth,
  isSameDay,
  isToday,
} from 'date-fns';
import { calendarApi, chatApi, parseApiError } from '../../api';
import { useAuthStore } from '../../store';
import { Header } from '../../components/layout';
import Button from '../../components/ui/Button';
import Modal from '../../components/ui/Modal';
import Input from '../../components/ui/Input';
import Card from '../../components/ui/Card';
import styles from './Calendar.module.css';

/**
 * Calendar Page
 * Displays user's calendar events with outfit suggestions
 * 
 * Backend APIs Used:
 * - GET /api/calendar?user_id={userId} - List events
 * - GET /api/calendar/month/{year}/{month}?user_id={userId} - Month view
 * - POST /api/calendar - Create event
 * - PUT /api/calendar/{eventId} - Update event
 * - DELETE /api/calendar/{eventId} - Delete event
 * - GET /api/calendar/{eventId}/outfit?user_id={userId} - Get outfit suggestion
 * - POST /api/chat/event-outfit - AI outfit suggestion for event
 */

const eventTypes = [
  { id: 'business', label: 'Business', color: '#2C3E50' },
  { id: 'casual', label: 'Casual', color: '#6B7C5A' },
  { id: 'formal', label: 'Formal', color: '#0E0E0E' },
  { id: 'date', label: 'Date Night', color: '#B87333' },
  { id: 'outdoor', label: 'Outdoor', color: '#4A7C59' },
  { id: 'party', label: 'Party', color: '#8B5CF6' },
];

const CalendarPage = () => {
  const { user } = useAuthStore();
  const userId = user?.user_id || localStorage.getItem('userId');
  
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEventModal, setShowEventModal] = useState(false);
  const [generatingOutfit, setGeneratingOutfit] = useState(null);
  const [newEvent, setNewEvent] = useState({
    title: '',
    date: '',
    time: '',
    type: 'casual',
    location: '',
  });

  useEffect(() => {
    fetchEvents();
  }, [currentMonth, userId]);

  /**
   * Fetch events for the current month
   * Uses GET /api/calendar/month/{year}/{month} or GET /api/calendar
   */
  const fetchEvents = async () => {
    if (!userId) {
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      const year = currentMonth.getFullYear();
      const month = currentMonth.getMonth() + 1; // API expects 1-12
      
      // Try month view endpoint first
      try {
        const response = await calendarApi.getMonthView(year, month, userId);
        setEvents(response.data.events || response.data || []);
        return;
      } catch (e) {
        // Fall back to date range query
        const start = format(startOfMonth(currentMonth), 'yyyy-MM-dd');
        const end = format(endOfMonth(currentMonth), 'yyyy-MM-dd');
        const response = await calendarApi.getEvents(userId, { start, end });
        setEvents(response.data.events || response.data || []);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
      // Mock data for demo when API is unavailable
      setEvents([
        {
          id: 1,
          title: 'Team Meeting',
          date: format(new Date(), 'yyyy-MM-dd'),
          time: '10:00',
          start_time: new Date().toISOString(),
          type: 'business',
          outfit: { id: 1, title: 'Smart Casual' },
        },
        {
          id: 2,
          title: 'Dinner Date',
          date: format(addDays(new Date(), 2), 'yyyy-MM-dd'),
          time: '19:00',
          start_time: addDays(new Date(), 2).toISOString(),
          type: 'date',
          outfit: { id: 2, title: 'Evening Elegant' },
        },
        {
          id: 3,
          title: 'Weekend Brunch',
          date: format(addDays(new Date(), 5), 'yyyy-MM-dd'),
          time: '11:00',
          start_time: addDays(new Date(), 5).toISOString(),
          type: 'casual',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const nextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));
  const prevMonth = () => setCurrentMonth(subMonths(currentMonth, 1));

  const renderCalendarDays = () => {
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(monthStart);
    const startDate = startOfWeek(monthStart);
    const endDate = endOfWeek(monthEnd);

    const days = [];
    let day = startDate;

    while (day <= endDate) {
      const currentDay = day;
      const dayEvents = events.filter((e) => {
        const eventDate = e.date || (e.start_time ? e.start_time.split('T')[0] : null);
        return eventDate === format(currentDay, 'yyyy-MM-dd');
      });

      days.push(
        <motion.div
          key={day.toString()}
          className={`${styles.day} ${
            !isSameMonth(day, monthStart) ? styles.disabled : ''
          } ${isSameDay(day, selectedDate) ? styles.selected : ''} ${
            isToday(day) ? styles.today : ''
          }`}
          onClick={() => setSelectedDate(currentDay)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <span className={styles.dayNumber}>{format(day, 'd')}</span>
          {dayEvents.length > 0 && (
            <div className={styles.dayEvents}>
              {dayEvents.slice(0, 3).map((event) => (
                <span
                  key={event.id}
                  className={styles.eventDot}
                  style={{
                    backgroundColor:
                      eventTypes.find((t) => t.id === event.type)?.color ||
                      '#6B7C5A',
                  }}
                />
              ))}
            </div>
          )}
        </motion.div>
      );

      day = addDays(day, 1);
    }

    return days;
  };

  const selectedDateEvents = events.filter((e) => {
    const eventDate = e.date || (e.start_time ? e.start_time.split('T')[0] : null);
    return eventDate === format(selectedDate, 'yyyy-MM-dd');
  });

  /**
   * Create a new event
   * POST /api/calendar
   */
  const handleCreateEvent = async () => {
    if (!userId || !newEvent.title) return;
    
    try {
      const eventData = {
        user_id: userId,
        title: newEvent.title,
        start_time: `${format(selectedDate, 'yyyy-MM-dd')}T${newEvent.time || '09:00'}:00`,
        end_time: `${format(selectedDate, 'yyyy-MM-dd')}T${newEvent.time ? 
          format(new Date(`2000-01-01T${newEvent.time}`).getTime() + 3600000, 'HH:mm') : '10:00'}:00`,
        location: newEvent.location,
        type: newEvent.type,
      };
      
      await calendarApi.createEvent(eventData);
      await fetchEvents();
      setShowEventModal(false);
      setNewEvent({ title: '', date: '', time: '', type: 'casual', location: '' });
    } catch (error) {
      console.error('Failed to create event:', error);
      // For demo, add locally
      const mockEvent = {
        id: Date.now(),
        title: newEvent.title,
        date: format(selectedDate, 'yyyy-MM-dd'),
        time: newEvent.time || '09:00',
        type: newEvent.type,
        location: newEvent.location,
      };
      setEvents([...events, mockEvent]);
      setShowEventModal(false);
      setNewEvent({ title: '', date: '', time: '', type: 'casual', location: '' });
    }
  };

  /**
   * Generate outfit suggestion for an event
   * Uses GET /api/calendar/{eventId}/outfit or POST /api/chat/event-outfit
   */
  const handleGenerateOutfit = async (event) => {
    setGeneratingOutfit(event.id);
    
    try {
      // Try dedicated endpoint first
      try {
        const response = await calendarApi.getEventOutfit(event.id, userId);
        // Update event with outfit
        setEvents(events.map(e => 
          e.id === event.id ? { ...e, outfit: response.data } : e
        ));
        return;
      } catch (e) {
        // Fall back to AI chat endpoint
        const response = await chatApi.getEventOutfit({
          event_title: event.title,
          event_time: event.time || '10:00 AM',
          location: event.location || '',
        });
        
        // Update event with generated outfit
        setEvents(events.map(e => 
          e.id === event.id ? { 
            ...e, 
            outfit: { 
              title: response.data?.outfit_name || 'Suggested Outfit',
              description: response.data?.description,
            } 
          } : e
        ));
      }
    } catch (error) {
      console.error('Failed to generate outfit:', error);
      // Mock outfit for demo
      setEvents(events.map(e => 
        e.id === event.id ? { 
          ...e, 
          outfit: { 
            id: Date.now(), 
            title: eventTypes.find(t => t.id === event.type)?.label + ' Look' 
          } 
        } : e
      ));
    } finally {
      setGeneratingOutfit(null);
    }
  };

  return (
    <div className={styles.page}>
      <Header />

      <main className={styles.main}>
        <div className={styles.container}>
          {/* Calendar Section */}
          <motion.section
            className={styles.calendarSection}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {/* Calendar Header */}
            <div className={styles.calendarHeader}>
              <h2 className={styles.monthTitle}>
                {format(currentMonth, 'MMMM yyyy')}
              </h2>
              <div className={styles.calendarNav}>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<ChevronLeft size={18} />}
                  onClick={prevMonth}
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCurrentMonth(new Date())}
                >
                  Today
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<ChevronRight size={18} />}
                  onClick={nextMonth}
                />
              </div>
            </div>

            {/* Weekday Headers */}
            <div className={styles.weekdays}>
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
                <div key={day} className={styles.weekday}>
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Grid */}
            <div className={styles.calendarGrid}>{renderCalendarDays()}</div>
          </motion.section>

          {/* Events Sidebar */}
          <motion.section
            className={styles.eventsSection}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <div className={styles.eventsHeader}>
              <div>
                <span className={styles.selectedDateLabel}>Events for</span>
                <h3 className={styles.selectedDate}>
                  {format(selectedDate, 'EEEE, MMMM d')}
                </h3>
              </div>
              <Button
                size="sm"
                icon={<Plus size={16} />}
                onClick={() => setShowEventModal(true)}
              >
                Add Event
              </Button>
            </div>

            <div className={styles.eventsList}>
              <AnimatePresence mode="wait">
                {selectedDateEvents.length > 0 ? (
                  selectedDateEvents.map((event, i) => (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <Card variant="default" padding="md" hoverable className={styles.eventCard}>
                        <div
                          className={styles.eventTypeIndicator}
                          style={{
                            backgroundColor:
                              eventTypes.find((t) => t.id === event.type)?.color,
                          }}
                        />
                        <div className={styles.eventContent}>
                          <h4 className={styles.eventTitle}>{event.title}</h4>
                          <div className={styles.eventMeta}>
                            <span className={styles.eventTime}>
                              <Clock size={14} />
                              {event.time || (event.start_time ? 
                                format(new Date(event.start_time), 'HH:mm') : '')}
                            </span>
                            {event.location && (
                              <span className={styles.eventLocation}>
                                <MapPin size={14} />
                                {event.location}
                              </span>
                            )}
                          </div>
                          {event.outfit ? (
                            <div className={styles.eventOutfit}>
                              <Shirt size={14} />
                              <span className={styles.outfitLabel}>Outfit:</span>
                              <span className={styles.outfitName}>{event.outfit.title}</span>
                            </div>
                          ) : (
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className={styles.generateBtn}
                              onClick={() => handleGenerateOutfit(event)}
                              loading={generatingOutfit === event.id}
                            >
                              {generatingOutfit === event.id ? 'Generating...' : 'Generate Outfit'}
                            </Button>
                          )}
                        </div>
                      </Card>
                    </motion.div>
                  ))
                ) : (
                  <motion.div
                    className={styles.emptyState}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <CalendarIcon size={32} />
                    <p>No events scheduled</p>
                    <Button
                      variant="outline"
                      size="sm"
                      icon={<Plus size={16} />}
                      onClick={() => setShowEventModal(true)}
                    >
                      Add Event
                    </Button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.section>
        </div>
      </main>

      {/* Add Event Modal */}
      <Modal
        isOpen={showEventModal}
        onClose={() => setShowEventModal(false)}
        title="Add New Event"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowEventModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateEvent} disabled={!newEvent.title}>
              Create Event
            </Button>
          </>
        }
      >
        <div className={styles.eventForm}>
          <Input
            label="Event Title"
            placeholder="e.g., Dinner with friends"
            value={newEvent.title}
            onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
          />
          <Input
            label="Time"
            type="time"
            value={newEvent.time}
            onChange={(e) => setNewEvent({ ...newEvent, time: e.target.value })}
          />
          <Input
            label="Location (optional)"
            placeholder="e.g., Downtown Restaurant"
            value={newEvent.location}
            onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
          />
          <div className={styles.eventTypeSelect}>
            <label className={styles.formLabel}>Event Type</label>
            <div className={styles.eventTypes}>
              {eventTypes.map((type) => (
                <button
                  key={type.id}
                  className={`${styles.eventTypeBtn} ${
                    newEvent.type === type.id ? styles.selected : ''
                  }`}
                  onClick={() => setNewEvent({ ...newEvent, type: type.id })}
                  style={{
                    '--type-color': type.color,
                  }}
                >
                  <span
                    className={styles.typeDot}
                    style={{ backgroundColor: type.color }}
                  />
                  {type.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default CalendarPage;
