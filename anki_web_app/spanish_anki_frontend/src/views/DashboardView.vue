<template>
  <div class="dashboard-view">
    <h1>Dashboard</h1>
    <div v-if="isLoading" class="loading-message">
      <p>Loading statistics...</p>
    </div>
    <div v-if="errorMessage" class="error-message">
      <p>{{ errorMessage }}</p>
    </div>
    <div v-if="!isLoading && statistics" class="statistics-grid">
      <div class="stat-card">
        <h2>Reviews Today</h2>
        <p>{{ statistics.reviews_today }}</p>
      </div>
      <div class="stat-card">
        <h2>New Cards Today</h2>
        <p>{{ statistics.new_cards_reviewed_today }}</p>
      </div>
      <div class="stat-card">
        <h2>Reviews This Week</h2>
        <p>{{ statistics.reviews_this_week }}</p>
      </div>
      <div class="stat-card">
        <h2>Total Reviews</h2>
        <p>{{ statistics.total_reviews_all_time }}</p>
      </div>
      <div class="stat-card">
        <h2>Average Score (All Cards)</h2>
        <p class="score-display">{{ formatScoreAsPercentage(statistics.overall_average_score) }}</p>
        <p v-if="statistics.overall_average_score !== null" class="score-subtitle">
          {{ formatScore(statistics.overall_average_score) }} / 1.00
        </p>
      </div>
      <div class="stat-card">
        <h2>Total Cards</h2>
        <p>{{ statistics.total_cards }}</p>
      </div>
      <div class="stat-card">
        <h2>Cards Learned</h2>
        <p>{{ statistics.cards_learned }} ({{ statistics.percentage_learned }}%)</p>
      </div>
      <div class="stat-card">
        <h2>Cards Mastered</h2>
        <p>{{ statistics.cards_mastered }}</p>
      </div>
    </div>
    <div v-if="!isLoading && !statistics && !errorMessage" class="no-data-message">
        <p>No statistics data available yet. Start reviewing some cards!</p>
    </div>

    <div v-if="!isLoading && studySessions && studySessions.length > 0" class="sessions-section">
      <h2>Study Sessions</h2>
      <div class="sessions-list">
        <div v-for="session in studySessions" :key="session.session_id" class="session-card">
          <div class="session-header-row">
            <span class="session-date">{{ formatSessionDate(session.start_time) }}</span>
            <span v-if="session.is_active" class="session-badge active">Active</span>
          </div>
          <div class="session-stats-row">
            <div class="session-stat">
              <span class="stat-label">Time:</span>
              <span class="stat-value">{{ formatTime(session.active_minutes) }}</span>
            </div>
            <div class="session-stat">
              <span class="stat-label">Cards:</span>
              <span class="stat-value">{{ session.cards_reviewed }}</span>
            </div>
            <div class="session-stat" v-if="session.average_score !== null">
              <span class="stat-label">Avg Score:</span>
              <span class="stat-value">{{ (session.average_score * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'DashboardView',
  data() {
    return {
      statistics: null,
      studySessions: [],
      isLoading: true,
      isLoadingSessions: false,
      errorMessage: ''
    };
  },
  methods: {
    async fetchStatistics() {
      this.isLoading = true;
      this.errorMessage = '';
      try {
        // Use Card statistics endpoint instead of Sentence endpoint
        const response = await ApiService.getCardStatistics();
        if (response.status === 200) {
          if (response.data) {
            this.statistics = response.data;
          } else {
            this.statistics = null;
          }
        } else {
          this.errorMessage = "Could not load statistics. The server didn't return valid data.";
          this.statistics = null;
        }
      } catch (error) {
        console.error("Error fetching statistics:", error);
        this.errorMessage = 'Failed to load statistics. Please check your connection or try again later.';
        this.statistics = null;
      }
      this.isLoading = false;
    },
    formatScore(score) {
        if (score === null || score === undefined) return 'N/A';
        return parseFloat(score).toFixed(2);
    },
    formatScoreAsPercentage(score) {
        if (score === null || score === undefined) return 'N/A';
        const percentage = parseFloat(score) * 100;
        return `${percentage.toFixed(1)}%`;
    },
    async fetchStudySessions() {
      this.isLoadingSessions = true;
      try {
        const response = await ApiService.getStudySessions();
        if (response && response.status === 200 && response.data) {
          this.studySessions = response.data.sessions || [];
        }
      } catch (error) {
        console.error("Error fetching study sessions:", error);
        // Don't show error for sessions, just log it
      } finally {
        this.isLoadingSessions = false;
      }
    },
    formatSessionDate(dateString) {
      if (!dateString) return 'N/A';
      const date = new Date(dateString);
      const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      };
      return date.toLocaleDateString(undefined, options);
    },
    formatTime(minutes) {
      if (!minutes && minutes !== 0) return '0:00';
      const hours = Math.floor(minutes / 60);
      const mins = Math.floor(minutes % 60);
      const secs = Math.floor((minutes % 1) * 60);
      if (hours > 0) {
        return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      }
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
  },
  mounted() {
    this.fetchStatistics();
    this.fetchStudySessions();
  },
};
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.loading-message, .error-message, .no-data-message {
  text-align: center;
  padding: 20px;
  background-color: #f0f0f0;
  border-radius: 8px;
  margin: 20px auto;
  max-width: 500px;
}

.error-message {
  color: red;
  background-color: #ffe0e0;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.stat-card {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.stat-card h2 {
  font-size: 1.1em;
  color: #333;
  margin-top: 0;
  margin-bottom: 10px;
}

.stat-card p {
  font-size: 1.8em;
  color: #007bff;
  margin: 0;
  font-weight: bold;
}

.score-display {
  font-size: 2.2em !important;
  color: #28a745 !important;
  margin-bottom: 5px !important;
}

.score-subtitle {
  font-size: 0.9em !important;
  color: #666 !important;
  font-weight: normal !important;
  margin-top: 5px !important;
}

.sessions-section {
  margin-top: 40px;
  padding-top: 30px;
  border-top: 2px solid #e0e0e0;
}

.sessions-section h2 {
  margin-bottom: 20px;
  color: #333;
  font-size: 1.5em;
}

.sessions-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.session-card {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.session-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.session-date {
  font-size: 0.95em;
  color: #555;
  font-weight: 500;
}

.session-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.8em;
  font-weight: bold;
}

.session-badge.active {
  background-color: #28a745;
  color: white;
}

.session-stats-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.session-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-stat .stat-label {
  font-size: 0.75em;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.session-stat .stat-value {
  font-size: 1.2em;
  font-weight: bold;
  color: #007bff;
}
</style> 