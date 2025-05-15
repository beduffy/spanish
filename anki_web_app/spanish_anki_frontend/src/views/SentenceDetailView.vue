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
      <h1>Sentence Detail (#{{ sentence.csv_number }})</h1>

      <div class="sentence-card main-details">
        <div class="detail-item"><strong>Key Spanish Word:</strong> {{ sentence.key_spanish_word }}</div>
        <div class="detail-item"><strong>Key Word Translation:</strong> {{ sentence.key_word_english_translation }}</div>
        <div class="detail-item spanish-text"><strong>Spanish Sentence:</strong> {{ sentence.spanish_sentence_example }}</div>
        <div class="detail-item english-text"><strong>English Sentence:</strong> {{ sentence.english_sentence_example }}</div>
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
    }
  },
  methods: {
    async fetchSentenceDetails(sentenceId) {
      this.isLoading = true;
      this.errorMessage = '';
      try {
        const response = await ApiService.getSentenceDetails(sentenceId);
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
  padding: 20px;
  font-family: Arial, sans-serif;
  max-width: 900px;
  margin: 0 auto;
}

.loading-message, .error-message, .no-data-message {
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

.back-link {
  display: inline-block;
  margin-bottom: 20px;
  color: #007bff;
  text-decoration: none;
}
.back-link:hover {
  text-decoration: underline;
}

.sentence-content h1 {
  margin-bottom: 20px;
  border-bottom: 2px solid #eee;
  padding-bottom: 10px;
}

.sentence-card {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 25px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.sentence-card h2 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 1.3em;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.detail-item {
  margin-bottom: 10px;
  line-height: 1.5;
}

.detail-item strong {
  color: #555;
}

.spanish-text, .english-text {
  font-size: 1.1em;
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
}

.review-history table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.review-history th, .review-history td {
  border: 1px solid #ddd;
  padding: 8px 10px;
  text-align: left;
  font-size: 0.9em;
}

.review-history thead {
  background-color: #f0f0f0;
}

.review-history tr:nth-child(even) {
  background-color: #f9f9f9;
}
</style> 