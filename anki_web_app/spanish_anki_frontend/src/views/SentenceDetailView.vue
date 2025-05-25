<template>
  <div class="sentence-detail-view">
    <div v-if="isLoading" class="loading-message">
      <p>Loading sentence details...</p>
    </div>
    <div v-if="errorMessage" class="error-message">
      <p>{{ errorMessage }}</p>
    </div>

    <div v-if="!isLoading && sentence" class="sentence-content">
      <router-link to="/sentences" class="back-link">&larr; Back to Sentence List</router-link>
      <h1>Sentence Detail (#{{ sentence.csv_number }}) <span :class="getDirectionBadgeClass(sentence.translation_direction)">{{ formatDirection(sentence.translation_direction) }}</span></h1>

      <div class="sentence-card main-details">
        <div class="detail-item"><strong>Prompt Key Word:</strong> {{ promptKeyWord }}</div>
        <div class="detail-item"><strong>Prompt Sentence:</strong> <span class="sentence-display">{{ promptSentence }}</span></div>
        <hr class="divider" />
        <div class="detail-item"><strong>Answer Key Word:</strong> {{ answerKeyWord }}</div>
        <div class="detail-item"><strong>Answer Sentence:</strong> <span class="sentence-display">{{ answerSentence }}</span></div>
        
        <div class="detail-item" v-if="sentence.base_comment"><strong>Base Comment:</strong> <pre>{{ sentence.base_comment }}</pre></div>
        <div class="detail-item" v-if="sentence.ai_explanation"><strong>AI Explanation:</strong> <pre>{{ sentence.ai_explanation }}</pre></div>
      </div>

      <div class="sentence-card srs-details">
        <h2>SRS Information</h2>
        <div class="detail-item"><strong>Status:</strong> {{ sentence.is_learning ? 'Learning' : 'Review' }}</div>
        <div class="detail-item"><strong>Next Review Date:</strong> {{ formatDate(sentence.next_review_date) }}</div>
        <div class="detail-item"><strong>Interval:</strong> {{ sentence.interval_days }} days</div>
        <div class="detail-item"><strong>Ease Factor:</strong> {{ sentence.ease_factor ? sentence.ease_factor.toFixed(2) : 'N/A' }}</div>
        <div class="detail-item"><strong>Consecutive Correct:</strong> {{ sentence.consecutive_correct_reviews }}</div>
        <div class="detail-item"><strong>Total Reviews:</strong> {{ sentence.total_reviews }}</div>
        <div class="detail-item"><strong>Avg. Score:</strong> {{ averageScore }}</div>
        <div class="detail-item"><strong>Created:</strong> {{ formatDateTime(sentence.creation_date) }}</div>
        <div class="detail-item"><strong>Last Modified:</strong> {{ formatDateTime(sentence.last_modified_date) }}</div>
      </div>

      <div v-if="sentence.reviews && sentence.reviews.length > 0" class="sentence-card review-history">
        <h2>Review History</h2>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Score</th>
              <th>Interval (Before)</th>
              <th>Ease (Before)</th>
              <th>Comment</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="review in sentence.reviews" :key="review.review_id">
              <td>{{ formatDateTime(review.review_timestamp) }}</td>
              <td>{{ review.user_score.toFixed(1) }}</td>
              <td>{{ review.interval_at_review }} days</td>
              <td>{{ review.ease_factor_at_review ? review.ease_factor_at_review.toFixed(2) : 'N/A' }}</td>
              <td><pre v-if="review.user_comment_addon">{{ review.user_comment_addon }}</pre></td>
            </tr>
          </tbody>
        </table>
      </div>
       <div v-else class="sentence-card review-history">
        <h2>Review History</h2>
        <p>No reviews recorded for this sentence yet.</p>
      </div>
    </div>
     <div v-if="!isLoading && !sentence && !errorMessage" class="no-data-message">
      <p>Sentence not found.</p>
      <router-link to="/sentences">Go back to Sentence List</router-link>
    </div>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'SentenceDetailView',
  props: {
    // If you want to use props from router, define id here
    // id: { type: [String, Number], required: true }
  },
  data() {
    return {
      sentence: null,
      isLoading: true,
      errorMessage: ''
    };
  },
  computed: {
    averageScore() {
      if (this.sentence && this.sentence.total_reviews > 0 && this.sentence.total_score_sum !== undefined) {
        return (this.sentence.total_score_sum / this.sentence.total_reviews).toFixed(2);
      }
      return 'N/A';
    },
    // Computed properties for dynamic display based on translation_direction
    isS2E() {
      return this.sentence && this.sentence.translation_direction === 'S2E';
    },
    promptKeyWord() {
      if (!this.sentence) return '';
      return this.isS2E ? this.sentence.key_spanish_word : this.sentence.key_word_english_translation;
    },
    promptSentence() {
      if (!this.sentence) return '';
      return this.isS2E ? this.sentence.spanish_sentence_example : this.sentence.english_sentence_example;
    },
    answerKeyWord() { // Renamed from answerKeyWordTranslation for clarity in detail view
      if (!this.sentence) return '';
      return this.isS2E ? this.sentence.key_word_english_translation : this.sentence.key_spanish_word;
    },
    answerSentence() { // Renamed from answerSentenceTranslation for clarity
      if (!this.sentence) return '';
      return this.isS2E ? this.sentence.english_sentence_example : this.sentence.spanish_sentence_example;
    }
  },
  methods: {
    async fetchSentenceDetails(sentenceId) {
      if (!sentenceId) {
        this.errorMessage = 'No sentence ID provided in the route.';
        this.isLoading = false;
        return;
      }
      this.isLoading = true;
      this.errorMessage = null;
      try {
        // Use ApiService.default.getSentenceDetails if that's what the transpiled/mocked version is
        const effectiveApiService = ApiService.default || ApiService;
        const response = await effectiveApiService.getSentenceDetails(sentenceId);
        if (response.status === 200 && response.data) {
          this.sentence = response.data;
        } else {
          this.errorMessage = `Could not load details for sentence ID ${sentenceId}. The server returned an unexpected response.`;
          this.sentence = null;
        }
      } catch (error) {
        console.error(`Error fetching details for sentence ID ${sentenceId}:`, error);
        if (error.response && error.response.status === 404) {
            this.errorMessage = `Sentence with ID ${sentenceId} not found.`;
        } else {
            this.errorMessage = `Failed to load details for sentence ID ${sentenceId}. Please check your connection or try again.`;
        }
        this.sentence = null;
      }
      this.isLoading = false;
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    },
    formatDateTime(dateTimeString) {
      if (!dateTimeString) return 'N/A';
      const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      return new Date(dateTimeString).toLocaleString(undefined, options);
    },
    // Copied from SentenceListView for consistency
    formatDirection(direction) {
      if (direction === 'S2E') return 'S2E';
      if (direction === 'E2S') return 'E2S';
      return direction;
    },
    getDirectionBadgeClass(direction) {
      return direction === 'S2E' ? 'badge-s2e' : 'badge-e2s';
    }
  },
  mounted() {
    const sentenceId = this.$route.params.id;
    if (sentenceId) {
      this.fetchSentenceDetails(sentenceId);
    } else {
      this.errorMessage = "No sentence ID provided in the route.";
      this.isLoading = false;
    }
  },
  // Watch for route changes if the user navigates from one detail view to another
  // directly (e.g. if we had next/prev sentence buttons on this page)
  // beforeRouteUpdate(to, from, next) {
  //   if (to.params.id !== from.params.id) {
  //     this.fetchSentenceDetails(to.params.id);
  //   }
  //   next();
  // }
};
</script>

<style scoped>
.sentence-detail-view {
  padding: 10px; /* Base padding for small screens */
  font-family: Arial, sans-serif;
  /* max-width: 900px; // Max-width will be handled by media query */
  margin: 0 auto;
  box-sizing: border-box;
}

.review-history {
  overflow-x: auto; /* Allow horizontal scrolling for the review history table container */
  -webkit-overflow-scrolling: touch; /* Smooth scrolling on iOS */
}

/* Badge styles copied from SentenceListView */
.badge-s2e,
.badge-e2s {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 0.65em; /* Further adjust for smaller screens */
  font-weight: bold;
  color: white;
  margin-left: 5px; /* Reduced margin */
  vertical-align: middle;
}

.badge-s2e {
  background-color: #007bff; /* Blue for S2E */
}

.badge-e2s {
  background-color: #28a745; /* Green for E2S */
}

.loading-message, .error-message, .no-data-message {
  text-align: center;
  padding: 15px; /* Adjusted padding */
  background-color: #f0f0f0;
  border-radius: 8px;
  margin: 15px auto; /* Adjusted margin */
  box-sizing: border-box;
}

.error-message {
  color: red;
  background-color: #ffe0e0;
}

.back-link {
  display: inline-block;
  margin-bottom: 15px; /* Adjusted margin */
  color: #007bff;
  text-decoration: none;
  font-size: 0.9em; /* Slightly smaller for mobile */
}
.back-link:hover {
  text-decoration: underline;
}

.sentence-content h1 {
  margin-bottom: 15px; /* Adjusted margin */
  border-bottom: 1px solid #eee; /* Lighter border */
  padding-bottom: 8px; /* Adjusted padding */
  font-size: 1.4em; /* Adjusted font size for mobile */
}

.sentence-card {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px; /* Reduced padding */
  margin-bottom: 20px; /* Reduced margin */
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.sentence-card h2 {
  margin-top: 0;
  margin-bottom: 12px; /* Adjusted margin */
  font-size: 1.2em; /* Adjusted font size */
  color: #333;
  border-bottom: 1px solid #f0f0f0; /* Lighter border */
  padding-bottom: 6px; /* Adjusted padding */
}

.divider {
  margin-top: 15px;
  margin-bottom: 15px;
  border: 0;
  border-top: 1px solid #eee;
}

.detail-item {
  margin-bottom: 8px; /* Reduced margin */
  line-height: 1.4; /* Adjusted line height */
  font-size: 0.9em; /* Base font size for detail items */
}

.detail-item strong {
  color: #444; /* Slightly darker for better contrast */
  margin-right: 5px;
}

.spanish-text, .english-text {
  font-size: 1.0em; /* Adjusted font size */
}

.sentence-display { /* Added for consistency with FlashcardView if specific styling is needed */
  font-size: 1.0em; /* Adjusted font size */
  display: block; /* Ensure it takes its own line if long */
  margin-top: 3px;
}

pre {
  white-space: pre-wrap; /* CSS3 */
  white-space: -moz-pre-wrap; /* Mozilla, since 1999 */
  white-space: -pre-wrap; /* Opera 4-6 */
  white-space: -o-pre-wrap; /* Opera 7 */
  word-wrap: break-word; /* Internet Explorer 5.5+ */
  background-color: #f9f9f9;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #eee;
  font-family: inherit;
  font-size: 0.9em; /* Ensure preformatted text is also responsive */
}

.review-history table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.review-history th, .review-history td {
  border: 1px solid #ddd;
  padding: 6px 8px; /* Reduced padding */
  text-align: left;
  font-size: 0.8em; /* Reduced font size */
  word-break: break-word;
}

.review-history thead {
  background-color: #f0f0f0;
}

.review-history tr:nth-child(even) {
  background-color: #f9f9f9;
}

/* Media Query for larger screens (tablets and desktops) */
@media (min-width: 768px) {
  .sentence-detail-view {
    padding: 20px; /* Original padding */
    max-width: 900px; /* Restore max-width */
  }

  .loading-message, .error-message, .no-data-message {
    padding: 20px; /* Original padding */
    margin: 20px auto; /* Original margin */
  }
  
  .back-link {
    margin-bottom: 20px; /* Original margin */
    font-size: 1em; /* Original font size */
  }

  .sentence-content h1 {
    margin-bottom: 20px; /* Original margin */
    border-bottom: 2px solid #eee; /* Original border */
    padding-bottom: 10px; /* Original padding */
    font-size: 1.6em; /* Original font size */
  }
  
  .badge-s2e, .badge-e2s {
    font-size: 0.7em; /* Original size */
    margin-left: 10px; /* Original margin */
  }

  .sentence-card {
    padding: 20px; /* Original padding */
    margin-bottom: 25px; /* Original margin */
  }

  .sentence-card h2 {
    margin-bottom: 15px; /* Original margin */
    font-size: 1.3em; /* Original font size */
    border-bottom: 1px solid #eee; /* Original border */
    padding-bottom: 8px; /* Original padding */
  }

  .detail-item {
    margin-bottom: 10px; /* Original margin */
    font-size: 1em; /* Original font size */
  }

  .spanish-text, .english-text, .sentence-display {
    font-size: 1.1em; /* Original font size */
  }
  
  pre {
    font-size: 1em; /* Original font size */
  }

  .review-history th, .review-history td {
    padding: 8px 10px; /* Original padding */
    font-size: 0.9em; /* Original font size */
  }
}

/* Minor adjustments for very small screens if needed */
@media (max-width: 360px) {
  .sentence-content h1 {
    font-size: 1.3em;
  }
  .badge-s2e, .badge-e2s {
    font-size: 0.6em;
  }
  .sentence-card h2 {
    font-size: 1.1em;
  }
  .detail-item {
    font-size: 0.85em;
  }
  .spanish-text, .english-text, .sentence-display {
    font-size: 0.95em;
  }
  .review-history th, .review-history td {
    font-size: 0.75em;
    padding: 5px;
  }
}
</style>