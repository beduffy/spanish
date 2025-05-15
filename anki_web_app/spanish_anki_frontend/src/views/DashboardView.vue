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
        <h2>Avg. Score</h2>
        <p>{{ formatScore(statistics.overall_average_score) }}</p>
      </div>
      <div class="stat-card">
        <h2>Total Sentences</h2>
        <p>{{ statistics.total_sentences }}</p>
      </div>
      <div class="stat-card">
        <h2>Sentences Learned</h2>
        <p>{{ statistics.sentences_learned }} ({{ statistics.percentage_learned }}%)</p>
      </div>
      <div class="stat-card">
        <h2>Sentences Mastered</h2>
        <p>{{ statistics.sentences_mastered }}</p>
      </div>
    </div>
    <div v-if="!isLoading && !statistics && !errorMessage" class="no-data-message">
        <p>No statistics data available yet. Start reviewing some cards!</p>
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
      isLoading: true,
      errorMessage: ''
    };
  },
  methods: {
    async fetchStatistics() {
      this.isLoading = true;
      this.errorMessage = '';
      try {
        const response = await ApiService.getStatistics();
        if (response.status === 200 && response.data) {
          this.statistics = response.data;
        } else {
          // Handle cases where data might be empty or response is not 200, though API should provide data or error.
          this.errorMessage = "Could not load statistics. The server didn't return valid data.";
        }
      } catch (error) {
        console.error("Error fetching statistics:", error);
        this.errorMessage = 'Failed to load statistics. Please check your connection or try again later.';
        this.statistics = null; // Clear any stale data
      }
      this.isLoading = false;
    },
    formatScore(score) {
        if (score === null || score === undefined) return 'N/A';
        return parseFloat(score).toFixed(2);
    }
  },
  mounted() {
    this.fetchStatistics();
  },
};
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
  font-family: Arial, sans-serif;
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
</style> 