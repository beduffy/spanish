<template>
  <div class="calendar-view">
    <h1>Study Calendar</h1>
    
    <div v-if="isLoading" class="loading-message">
      <p>Loading calendar data...</p>
    </div>

    <div v-if="errorMessage" class="error-message">
      <p>{{ errorMessage }}</p>
    </div>

    <div v-if="!isLoading && !errorMessage" class="calendar-container">
      <div class="calendar-header">
        <button @click="previousMonth" class="nav-button">‹</button>
        <h2>{{ currentMonthYear }}</h2>
        <button @click="nextMonth" class="nav-button">›</button>
      </div>

      <div class="calendar-grid">
        <div class="calendar-weekday" v-for="day in weekdays" :key="day">{{ day }}</div>
        <div
          v-for="day in calendarDays"
          :key="day.date"
          class="calendar-day"
          :class="{
            'other-month': !day.isCurrentMonth,
            'today': day.isToday,
            'has-sessions': day.sessionCount > 0
          }"
          @click="selectDate(day.date)"
        >
          <div class="day-number">{{ day.dayNumber }}</div>
          <div v-if="day.sessionCount > 0" class="session-indicator">
            <span class="session-count">{{ day.sessionCount }}</span>
            <span class="session-label">session{{ day.sessionCount !== 1 ? 's' : '' }}</span>
          </div>
          <div v-if="day.cardsReviewed > 0" class="cards-count">
            {{ day.cardsReviewed }} card{{ day.cardsReviewed !== 1 ? 's' : '' }}
          </div>
        </div>
      </div>

      <div v-if="selectedDateData" class="selected-date-details">
        <h3>{{ formatSelectedDate(selectedDate) }}</h3>
        <div v-if="selectedDateData.sessions.length > 0" class="date-sessions">
          <div v-for="session in selectedDateData.sessions" :key="session.session_id" class="date-session-item">
            <div class="session-time">{{ formatTime(session.start_time) }}</div>
            <div class="session-info">
              <span>{{ formatTime(session.active_minutes) }}</span>
              <span>{{ session.cards_reviewed }} cards</span>
              <span v-if="session.average_score !== null">{{ (session.average_score * 100).toFixed(0) }}% avg</span>
            </div>
          </div>
        </div>
        <div v-else class="no-sessions">
          No study sessions on this date.
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'CalendarView',
  data() {
    return {
      currentDate: new Date(),
      selectedDate: null,
      selectedDateData: null,
      studySessions: [],
      isLoading: true,
      errorMessage: '',
      weekdays: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    };
  },
  computed: {
    currentMonthYear() {
      return this.currentDate.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
    },
    calendarDays() {
      const year = this.currentDate.getFullYear();
      const month = this.currentDate.getMonth();
      
      // First day of the month
      const firstDay = new Date(year, month, 1);
      const firstDayOfWeek = firstDay.getDay();
      
      // Last day of the month
      const lastDay = new Date(year, month + 1, 0);
      const daysInMonth = lastDay.getDate();
      
      // Previous month's days to fill the first week
      const prevMonth = new Date(year, month, 0);
      const daysInPrevMonth = prevMonth.getDate();
      
      const days = [];
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      // Previous month days
      for (let i = firstDayOfWeek - 1; i >= 0; i--) {
        const date = new Date(year, month - 1, daysInPrevMonth - i);
        days.push(this.createDayObject(date, false, today));
      }
      
      // Current month days
      for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        days.push(this.createDayObject(date, true, today));
      }
      
      // Next month days to fill the last week
      const remainingDays = 42 - days.length; // 6 weeks * 7 days
      for (let day = 1; day <= remainingDays; day++) {
        const date = new Date(year, month + 1, day);
        days.push(this.createDayObject(date, false, today));
      }
      
      return days;
    },
  },
  methods: {
    createDayObject(date, isCurrentMonth, today) {
      const dateStr = date.toISOString().split('T')[0];
      const sessionsForDay = this.studySessions.filter(s => {
        const sessionDate = new Date(s.start_time).toISOString().split('T')[0];
        return sessionDate === dateStr;
      });
      
      const cardsReviewed = sessionsForDay.reduce((sum, s) => sum + s.cards_reviewed, 0);
      
      return {
        date: dateStr,
        dayNumber: date.getDate(),
        isCurrentMonth,
        isToday: dateStr === today.toISOString().split('T')[0],
        sessionCount: sessionsForDay.length,
        cardsReviewed,
        sessions: sessionsForDay,
      };
    },
    async fetchStudySessions() {
      this.isLoading = true;
      this.errorMessage = '';
      try {
        const response = await ApiService.getStudySessions();
        if (response.status === 200 && response.data) {
          this.studySessions = response.data.sessions || [];
        }
      } catch (error) {
        console.error("Error fetching study sessions:", error);
        this.errorMessage = 'Failed to load calendar data. Please try again later.';
      } finally {
        this.isLoading = false;
      }
    },
    previousMonth() {
      this.currentDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() - 1, 1);
      this.selectedDate = null;
      this.selectedDateData = null;
    },
    nextMonth() {
      this.currentDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 1);
      this.selectedDate = null;
      this.selectedDateData = null;
    },
    selectDate(dateStr) {
      this.selectedDate = dateStr;
      const dayData = this.calendarDays.find(d => d.date === dateStr);
      if (dayData) {
        this.selectedDateData = dayData;
      }
    },
    formatSelectedDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleDateString(undefined, { 
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    },
    formatTime(timeOrMinutes) {
      if (typeof timeOrMinutes === 'number') {
        // It's minutes
        const hours = Math.floor(timeOrMinutes / 60);
        const mins = Math.floor(timeOrMinutes % 60);
        const secs = Math.floor((timeOrMinutes % 1) * 60);
        if (hours > 0) {
          return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${mins}:${secs.toString().padStart(2, '0')}`;
      } else {
        // It's a datetime string
        const date = new Date(timeOrMinutes);
        return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
      }
    },
  },
  mounted() {
    this.fetchStudySessions();
  },
};
</script>

<style scoped>
.calendar-view {
  padding: 20px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  max-width: 1200px;
  margin: 0 auto;
}

.loading-message, .error-message {
  text-align: center;
  padding: 20px;
  background-color: #f0f0f0;
  border-radius: 8px;
  margin: 20px auto;
}

.error-message {
  color: red;
  background-color: #ffe0e0;
}

.calendar-container {
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.calendar-header h2 {
  margin: 0;
  font-size: 1.5em;
  color: #333;
}

.nav-button {
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 1.2em;
  transition: background-color 0.2s;
}

.nav-button:hover {
  background-color: #0056b3;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  margin-bottom: 20px;
}

.calendar-weekday {
  text-align: center;
  font-weight: bold;
  color: #666;
  padding: 10px;
  font-size: 0.9em;
}

.calendar-day {
  aspect-ratio: 1;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  background-color: #fff;
}

.calendar-day:hover {
  background-color: #f0f8ff;
  border-color: #007bff;
}

.calendar-day.other-month {
  opacity: 0.4;
  background-color: #f9f9f9;
}

.calendar-day.today {
  border: 2px solid #007bff;
  background-color: #e6f3ff;
}

.calendar-day.has-sessions {
  background-color: #d4edda;
  border-color: #28a745;
}

.day-number {
  font-weight: bold;
  font-size: 1.1em;
  margin-bottom: 4px;
}

.session-indicator {
  margin-top: auto;
  text-align: center;
  font-size: 0.75em;
}

.session-count {
  display: block;
  font-weight: bold;
  color: #28a745;
  font-size: 1.2em;
}

.session-label {
  color: #666;
  font-size: 0.85em;
}

.cards-count {
  font-size: 0.7em;
  color: #666;
  margin-top: 4px;
  text-align: center;
}

.selected-date-details {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 2px solid #e0e0e0;
}

.selected-date-details h3 {
  margin-bottom: 15px;
  color: #333;
}

.date-sessions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.date-session-item {
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-time {
  font-weight: bold;
  color: #007bff;
}

.session-info {
  display: flex;
  gap: 15px;
  font-size: 0.9em;
  color: #666;
}

.no-sessions {
  text-align: center;
  padding: 20px;
  color: #999;
  font-style: italic;
}
</style>
