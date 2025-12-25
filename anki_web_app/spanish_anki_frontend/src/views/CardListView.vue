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
          <tr v-for="card in cards" :key="card.card_id">
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
            <td>{{ card.total_reviews }}</td>
            <td>
              <router-link :to="{ name: 'CardEditor', params: { id: card.card_id } }" class="action-link">Edit</router-link>
              <button @click="confirmDelete(card)" class="action-link delete-btn">Delete</button>
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
</style>
