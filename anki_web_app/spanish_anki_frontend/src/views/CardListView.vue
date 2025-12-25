<template>
  <div class="card-list-view">
    <div class="header-actions">
      <h1>All Cards</h1>
      <div class="action-buttons">
        <router-link to="/cards/create" class="btn btn-primary">Create Card</router-link>
        <router-link to="/cards/import" class="btn btn-secondary">Import Cards</router-link>
      </div>
    </div>

    <div v-if="isLoading" class="loading-message">
      <p>Loading cards...</p>
    </div>
    <div v-if="errorMessage" class="error-message">
      <p>{{ errorMessage }}</p>
    </div>

    <div v-if="!isLoading && cards.length > 0" class="cards-container">
      <p class="total-count">Total cards: {{ totalItems }}</p>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Front</th>
            <th>Back</th>
            <th>Tags</th>
            <th>Mastery</th>
            <th>Status</th>
            <th>Next Review</th>
            <th>Reviews</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="card in cards" :key="card.card_id">
            <tr @click="toggleReviews(card)" class="card-row" :class="{ 'expanded': expandedCards[card.card_id] }">
              <td>{{ card.card_id }}</td>
              <td class="text-preview">{{ card.front }}</td>
              <td class="text-preview">{{ card.back }}</td>
              <td>
                <span v-for="tag in card.tags" :key="tag" class="tag-badge">{{ tag }}</span>
                <span v-if="!card.tags || card.tags.length === 0">-</span>
              </td>
              <td>
                <span v-if="card.mastery_level" :class="`badge-mastery badge-mastery-${card.mastery_level.color}`" :title="card.mastery_level.indicator || ''">
                  {{ card.mastery_level.level }}
                  <span v-if="card.mastery_level.score !== null" class="mastery-score">
                    ({{ card.mastery_level.score.toFixed(2) }})
                  </span>
                </span>
                <span v-else>-</span>
              </td>
              <td>
                <span :class="card.is_learning ? 'badge-learning' : 'badge-review'">
                  {{ card.is_learning ? 'Learning' : 'Review' }}
                </span>
              </td>
              <td>{{ formatDate(card.next_review_date) }}</td>
              <td>
                <button @click.stop="toggleReviews(card)" class="reviews-btn" :class="{ 'has-reviews': card.total_reviews > 0 }">
                  {{ card.total_reviews }} {{ card.total_reviews === 1 ? 'review' : 'reviews' }}
                  <span class="expand-icon">{{ expandedCards[card.card_id] ? '▼' : '▶' }}</span>
                </button>
              </td>
              <td @click.stop>
                <router-link :to="{ name: 'CardEditor', params: { id: card.card_id } }" class="action-link">Edit</router-link>
                <button @click="confirmDelete(card)" class="action-link delete-btn">Delete</button>
              </td>
            </tr>
            <tr v-if="expandedCards[card.card_id]" class="reviews-row">
              <td colspan="9" class="reviews-cell">
                <div v-if="loadingReviews[card.card_id]" class="loading-reviews">
                  Loading reviews...
                </div>
                <div v-else-if="cardReviews[card.card_id] && cardReviews[card.card_id].length > 0" class="reviews-container">
                  <h4>Review History ({{ cardReviews[card.card_id].length }})</h4>
                  <table class="reviews-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Score</th>
                        <th>Interval</th>
                        <th>Ease Factor</th>
                        <th>Comment</th>
                        <th>Typed Input</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="review in cardReviews[card.card_id]" :key="review.review_id">
                        <td>{{ formatDateTime(review.review_timestamp) }}</td>
                        <td>
                          <span class="score-badge" :class="getScoreClass(review.user_score)">
                            {{ (review.user_score * 100).toFixed(0) }}%
                          </span>
                        </td>
                        <td>{{ review.interval_at_review }} days</td>
                        <td>{{ review.ease_factor_at_review ? review.ease_factor_at_review.toFixed(2) : 'N/A' }}</td>
                        <td class="comment-cell">{{ review.user_comment_addon || '-' }}</td>
                        <td class="typed-input-cell">{{ review.typed_input || '-' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div v-else class="no-reviews">
                  No reviews yet for this card.
                </div>
              </td>
            </tr>
          </template>
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
    <div v-if="!isLoading && cards.length === 0 && !errorMessage" class="no-data-message">
      <p>No cards found. <router-link to="/cards/create">Create your first card</router-link> or <router-link to="/cards/import">import from CSV</router-link>.</p>
    </div>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'CardListView',
  data() {
    return {
      cards: [],
      isLoading: true,
      isFetchingPage: false,
      errorMessage: '',
      currentPage: 1,
      totalPages: 0,
      totalItems: 0,
      expandedCards: {},
      cardReviews: {},
      loadingReviews: {},
    };
  },
  methods: {
    async fetchCards(page) {
      if (this.isFetchingPage) return;
      this.isLoading = this.currentPage === 1;
      this.isFetchingPage = true;
      this.errorMessage = '';
      try {
        const response = await ApiService.getAllCards(page);
        if (response.status === 200 && response.data) {
          this.cards = response.data.results || [];
          this.totalPages = Number.isInteger(response.data.total_pages) ? response.data.total_pages : 0;
          this.totalItems = Number.isInteger(response.data.count) ? response.data.count : 0;
          this.currentPage = page;
        } else {
          this.errorMessage = "Could not load cards. The server didn't return valid data.";
        }
      } catch (error) {
        console.error(`Error fetching cards (page ${page}):`, error);
        this.errorMessage = 'Failed to load cards. Please check your connection or try again later.';
        this.cards = [];
        this.totalPages = 0;
        this.totalItems = 0;
      } finally {
        this.isLoading = false;
        this.isFetchingPage = false;
      }
    },
    goToPage(page) {
      if (page >= 1 && page <= this.totalPages && page !== this.currentPage) {
        this.fetchCards(page);
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    },
    async confirmDelete(card) {
      if (confirm(`Delete card "${card.front.substring(0, 50)}..."? This will also delete the reverse card if it exists.`)) {
        try {
          await ApiService.deleteCard(card.card_id);
          this.fetchCards(this.currentPage);
        } catch (error) {
          console.error('Error deleting card:', error);
          alert('Failed to delete card. Please try again.');
        }
      }
    },
    async toggleReviews(card) {
      const cardId = card.card_id;
      
      // If already expanded, collapse
      if (this.expandedCards[cardId]) {
        this.$set(this.expandedCards, cardId, false);
        return;
      }
      
      // Expand and fetch reviews if not already loaded
      this.$set(this.expandedCards, cardId, true);
      
      if (!this.cardReviews[cardId] && !this.loadingReviews[cardId]) {
        this.$set(this.loadingReviews, cardId, true);
        try {
          const response = await ApiService.getCardDetails(cardId);
          if (response.status === 200 && response.data && response.data.reviews) {
            // Sort reviews by timestamp (newest first)
            const reviews = [...response.data.reviews].sort((a, b) => {
              return new Date(b.review_timestamp) - new Date(a.review_timestamp);
            });
            this.$set(this.cardReviews, cardId, reviews);
          } else {
            this.$set(this.cardReviews, cardId, []);
          }
        } catch (error) {
          console.error(`Error fetching reviews for card ${cardId}:`, error);
          this.$set(this.cardReviews, cardId, []);
        } finally {
          this.$set(this.loadingReviews, cardId, false);
        }
      }
    },
    formatDateTime(dateString) {
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
    getScoreClass(score) {
      if (score >= 0.9) return 'score-excellent';
      if (score >= 0.7) return 'score-good';
      if (score >= 0.5) return 'score-fair';
      return 'score-poor';
    }
  },
  mounted() {
    this.fetchCards(this.currentPage);
  },
};
</script>

<style scoped>
.card-list-view {
  padding: 20px;
  font-family: Arial, sans-serif;
  max-width: 1400px;
  margin: 0 auto;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 10px 20px;
  border-radius: 4px;
  text-decoration: none;
  font-weight: bold;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
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

.text-preview {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

tr:nth-child(even) {
  background-color: #f9f9f9;
}

tr:hover {
  background-color: #f1f1f1;
}

.tag-badge {
  display: inline-block;
  background-color: #e0e0e0;
  color: #333;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.8em;
  margin-right: 5px;
}

.badge-learning {
  background-color: #ffc107;
  color: #000;
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 0.8em;
  font-weight: bold;
}

.badge-review {
  background-color: #28a745;
  color: white;
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 0.8em;
  font-weight: bold;
}

.badge-mastery {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: bold;
  display: inline-block;
}

.badge-mastery-green {
  background-color: #28a745;
  color: white;
}

.badge-mastery-blue {
  background-color: #007bff;
  color: white;
}

.badge-mastery-cyan {
  background-color: #17a2b8;
  color: white;
}

.badge-mastery-yellow {
  background-color: #ffc107;
  color: #000;
}

.badge-mastery-orange {
  background-color: #fd7e14;
  color: white;
}

.badge-mastery-gray {
  background-color: #6c757d;
  color: white;
}

.mastery-score {
  font-size: 0.85em;
  opacity: 0.9;
  margin-left: 4px;
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
  margin-right: 10px;
  cursor: pointer;
}

.action-link:hover {
  text-decoration: underline;
}

.delete-btn {
  color: #dc3545;
  background: none;
  border: none;
  padding: 0;
  font-size: inherit;
}

.delete-btn:hover {
  color: #c82333;
}

.card-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.card-row:hover {
  background-color: #f0f8ff;
}

.card-row.expanded {
  background-color: #e6f3ff;
}

.reviews-btn {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.2s;
}

.reviews-btn:hover {
  background-color: #e6f3ff;
}

.reviews-btn.has-reviews {
  font-weight: bold;
}

.expand-icon {
  font-size: 0.8em;
  transition: transform 0.2s;
}

.reviews-row {
  background-color: #f9f9f9;
}

.reviews-cell {
  padding: 20px !important;
  background-color: #f9f9f9;
}

.loading-reviews {
  text-align: center;
  padding: 20px;
  color: #666;
}

.reviews-container {
  max-width: 100%;
  overflow-x: auto;
}

.reviews-container h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 1.1em;
}

.reviews-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.reviews-table thead {
  background-color: #6c757d;
  color: white;
}

.reviews-table th,
.reviews-table td {
  padding: 10px 12px;
  border: 1px solid #ddd;
  text-align: left;
  font-size: 0.85em;
}

.reviews-table tbody tr:nth-child(even) {
  background-color: #f9f9f9;
}

.reviews-table tbody tr:hover {
  background-color: #f1f1f1;
}

.comment-cell,
.typed-input-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.score-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: bold;
  font-size: 0.9em;
}

.score-excellent {
  background-color: #28a745;
  color: white;
}

.score-good {
  background-color: #17a2b8;
  color: white;
}

.score-fair {
  background-color: #ffc107;
  color: #000;
}

.score-poor {
  background-color: #dc3545;
  color: white;
}

.no-reviews {
  text-align: center;
  padding: 20px;
  color: #666;
  font-style: italic;
}
</style>
