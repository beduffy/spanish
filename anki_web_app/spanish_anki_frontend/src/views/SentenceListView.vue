<template>
  <div class="sentence-list-view">
    <h1>All Sentences</h1>

    <div v-if="isLoading" class="loading-message">
      <p>Loading sentences...</p>
    </div>
    <div v-if="errorMessage" class="error-message">
      <p>{{ errorMessage }}</p>
    </div>

    <div v-if="!isLoading && sentences.length > 0" class="sentences-container">
      <p class="total-count">Total sentence cards: {{ totalItems }}</p>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Direction</th>
            <th>Prompt Key Word</th>
            <th>Prompt Sentence</th>
            <th>Answer Sentence</th>
            <th>Learned?</th>
            <th>Next Review</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sentence in sentences" :key="sentence.sentence_id">
            <td>{{ sentence.csv_number }}</td>
            <td><span :class="getDirectionBadgeClass(sentence.translation_direction)">{{ formatDirection(sentence.translation_direction) }}</span></td>
            <td>{{ getPromptKeyWord(sentence) }}</td>
            <td>{{ getPromptSentence(sentence) }}</td>
            <td>{{ getAnswerSentence(sentence) }}</td>
            <td>{{ sentence.is_learning ? 'Learning' : 'Review' }}</td>
            <td>{{ formatDate(sentence.next_review_date) }}</td>
            <td>
              <router-link :to="{ name: 'SentenceDetailView', params: { id: sentence.sentence_id } }" class="action-link">View Details</router-link>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination-controls">
        <button @click="goToPage(currentPage - 1)" :disabled="currentPage === 1 || isFetchingPage">
          Previous
        </button>
        <span>Page {{ currentPage }} of {{ totalPages }}</span>
        <button @click="goToPage(currentPage + 1)" :disabled="currentPage === totalPages || isFetchingPage">
          Next
        </button>
      </div>
    </div>
    <div v-if="!isLoading && sentences.length === 0 && !errorMessage" class="no-data-message">
      <p>No sentences found in the database. Try importing your CSV.</p>
    </div>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'SentenceListView',
  data() {
    return {
      sentences: [],
      isLoading: true,
      isFetchingPage: false, // To disable pagination buttons during fetch
      errorMessage: '',
      currentPage: 1,
      totalPages: 0,
      totalItems: 0,
    };
  },
  methods: {
    async fetchSentences(page) {
      if (this.isFetchingPage) return; // Prevent multiple fetches
      this.isLoading = this.currentPage === 1; // Show main loading only for initial load
      this.isFetchingPage = true;
      this.errorMessage = '';
      try {
        const response = await ApiService.getAllSentences(page);
        if (response.status === 200 && response.data) {
          this.sentences = response.data.results || []; // Default to empty array if results is null/undefined
          this.totalPages = Number.isInteger(response.data.total_pages) ? response.data.total_pages : 0;
          this.totalItems = Number.isInteger(response.data.count) ? response.data.count : 0;
          this.currentPage = page;
        } else {
          this.errorMessage = "Could not load sentences. The server didn't return valid data.";
        }
      } catch (error) {
        console.error(`Error fetching sentences (page ${page}):`, error);
        this.errorMessage = 'Failed to load sentences. Please check your connection or try again later.';
        // Optionally, clear sentences or handle specific errors
        this.sentences = [];
        this.totalPages = 0;
        this.totalItems = 0;
      } finally {
        this.isLoading = false;
        this.isFetchingPage = false;
      }
    },
    goToPage(page) {
      if (page >= 1 && page <= this.totalPages && page !== this.currentPage) {
        this.fetchSentences(page);
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    },
    formatDirection(direction) {
      if (direction === 'S2E') return 'S2E'; // Spanish to English
      if (direction === 'E2S') return 'E2S'; // English to Spanish
      return direction; // Fallback
    },
    getDirectionBadgeClass(direction) {
      return direction === 'S2E' ? 'badge-s2e' : 'badge-e2s';
    },
    // Helper methods to get prompt/answer based on direction for list view consistency
    getPromptKeyWord(sentence) {
      if (!sentence) return '';
      return sentence.translation_direction === 'S2E' ? sentence.key_spanish_word : sentence.key_word_english_translation;
    },
    getPromptSentence(sentence) {
      if (!sentence) return '';
      return sentence.translation_direction === 'S2E' ? sentence.spanish_sentence_example : sentence.english_sentence_example;
    },
    getAnswerSentence(sentence) {
      if (!sentence) return '';
      return sentence.translation_direction === 'S2E' ? sentence.english_sentence_example : sentence.spanish_sentence_example;
    }
  },
  mounted() {
    this.fetchSentences(this.currentPage);
  },
  watch: {
    // Watch for route query changes if you implement page numbers in URL
    // '$route.query.page': function(newPage) {
    //   this.goToPage(parseInt(newPage) || 1);
    // }
  }
};
</script>

<style scoped>
.sentence-list-view {
  padding: 20px;
  font-family: Arial, sans-serif;
  max-width: 1200px;
  margin: 0 auto;
}

.badge-s2e,
.badge-e2s {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 0.8em;
  font-weight: bold;
  color: white;
}

.badge-s2e {
  background-color: #007bff; /* Blue for S2E */
}

.badge-e2s {
  background-color: #28a745; /* Green for E2S */
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

.total-count {
  text-align: right;
  margin-bottom: 10px;
  font-size: 0.9em;
  color: #555;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

thead {
  background-color: #007bff;
  color: white;
}

th, td {
  padding: 10px 12px;
  border: 1px solid #ddd;
  text-align: left;
  font-size: 0.9em;
}

tr:nth-child(even) {
  background-color: #f9f9f9;
}

tr:hover {
  background-color: #f1f1f1;
}

.pagination-controls {
  margin-top: 20px;
  text-align: center;
}

.pagination-controls button {
  padding: 8px 15px;
  margin: 0 5px;
  border: 1px solid #007bff;
  background-color: #fff;
  color: #007bff;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.pagination-controls button:hover:not(:disabled) {
  background-color: #007bff;
  color: white;
}

.pagination-controls button:disabled {
  border-color: #ccc;
  color: #ccc;
  cursor: not-allowed;
}

.pagination-controls span {
  margin: 0 10px;
  vertical-align: middle;
}

.action-link {
  color: #007bff;
  text-decoration: none;
  margin-left: 10px;
}

.action-link:hover {
  text-decoration: underline;
}
</style> 