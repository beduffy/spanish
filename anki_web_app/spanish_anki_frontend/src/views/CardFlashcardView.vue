<template>
  <div class="flashcard-view">
    <h1>Card Review</h1>

    <div v-if="isLoading" class="loading-message">
      <p>Loading next card...</p>
    </div>

    <div v-if="!isLoading && !currentCard && !allCardsDone" class="no-cards-message">
      <p>No cards due for review right now. Check back later!</p>
    </div>

    <div v-if="allCardsDone" class="all-done-message">
      <p>Congratulations! You've reviewed all available cards for now!</p>
    </div>

    <div v-if="!isLoading && currentCard" class="flashcard-container">
      <div class="card-header">
        <span class="card-type-badge">Card</span>
        <span class="card-csv-number">#{{ currentCard.card_id }}</span>
      </div>

      <!-- Front of the Card -->
      <div class="card-front">
        <p class="sentence-display" style="white-space: pre-wrap;">{{ currentCard.front }}</p>
        <p v-if="currentCard.last_reviewed_date" class="last-reviewed">
          Last reviewed: {{ formatDate(currentCard.last_reviewed_date) }}
        </p>
      </div>

      <div class="review-inputs">
        <div>
          <label for="typedInput">Type your answer (optional):</label>
          <textarea id="typedInput" v-model="typedInput" rows="2"></textarea>
        </div>
      </div>

      <!-- Answer Button -->
      <button v-if="!showAnswer" @click="revealAnswer" class="action-button">Show Answer</button>

      <!-- Back of the Card (shown after clicking "Show Answer") -->
      <div v-if="showAnswer" class="card-back">
        <hr>
        <p style="white-space: pre-wrap;"><strong>Answer:</strong> {{ currentCard.back }}</p>

        <div v-if="currentCard.notes" class="comments-section">
          <strong>Notes:</strong>
          <p style="white-space: pre-wrap;">{{ currentCard.notes }}</p>
        </div>

        <div class="card-stats">
          <div class="stat-item">
            <strong>Status:</strong> 
            <span :class="currentCard.is_learning ? 'status-learning' : 'status-review'">
              {{ currentCard.is_learning ? 'Learning' : 'Review' }}
            </span>
          </div>
          <div class="stat-item" v-if="currentCard.total_reviews > 0">
            <strong>Reviews:</strong> {{ currentCard.total_reviews }}
            <span v-if="currentCard.average_score !== null" class="avg-score">
              (Avg: {{ (currentCard.average_score * 100).toFixed(0) }}%)
            </span>
          </div>
          <div class="stat-item" v-if="currentCard.next_review_date">
            <strong>Next review:</strong> {{ formatDate(currentCard.next_review_date) }}
            <span v-if="getDaysUntilReview(currentCard.next_review_date) !== null" class="days-until">
              ({{ getDaysUntilReview(currentCard.next_review_date) }})
            </span>
          </div>
          <div class="stat-item ease-factor-info" title="Ease Factor: Controls how quickly the review interval grows. Higher = longer intervals between reviews. Increases with good scores, decreases with poor scores.">
            <strong>Ease Factor:</strong> {{ currentCard.ease_factor ? currentCard.ease_factor.toFixed(2) : '2.50' }}
            <span class="info-icon" title="Ease Factor controls how quickly review intervals grow. Higher values mean longer intervals between reviews.">ℹ️</span>
          </div>
        </div>

        <div class="review-inputs">
          <div>
            <label for="userScore">Your Score (0.0 - 1.0):</label>
            <div class="score-quick-picks">
              <button
                v-for="score in scoreShortcuts"
                :key="score"
                @click="setScore(score)"
                :class="['score-button', { 'score-button-active': userScore === score }]"
                type="button"
              >
                {{ score }}
              </button>
            </div>
            <input type="number" id="userScore" v-model.number="userScore" min="0" max="1" step="0.1" class="score-input" />
          </div>
          <div>
            <label for="userComment">Your Comment (optional):</label>
            <textarea id="userComment" v-model="userComment" rows="3"></textarea>
          </div>
          <button @click="submitReviewHandler" :disabled="isSubmitting" class="action-button">
            {{ isSubmitting ? 'Submitting...' : 'Submit & Next' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="errorMessage && !isLoading" class="error-message central-error">
      <p>{{ errorMessage }}</p>
    </div>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'CardFlashcardView',
  data() {
    return {
      currentCard: null,
      showAnswer: false,
      typedInput: '',
      userScore: 1.0,
      userComment: '',
      isLoading: true,
      isSubmitting: false,
      allCardsDone: false,
      errorMessage: '',
      scoreShortcuts: [0, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0],
    };
  },
  methods: {
    async fetchNextCard() {
      this.isLoading = true;
      this.errorMessage = '';
      this.allCardsDone = false;
      try {
        const response = await ApiService.getNextCardV2();
        if (response.status === 200 && response.data) {
          this.currentCard = response.data;
          this.showAnswer = false;
          this.typedInput = '';
          this.userScore = 1.0;
          this.userComment = '';
        } else if (response.status === 204) {
          this.currentCard = null;
          this.allCardsDone = true;
        }
      } catch (error) {
        console.error("Error fetching next card:", error);
        this.errorMessage = 'Failed to load the next card. Please check your connection or try again later.';
        if (error.response && error.response.status === 204) {
          this.currentCard = null;
          this.allCardsDone = true;
        } else {
          this.currentCard = null;
        }
      } finally {
        this.isLoading = false;
      }
    },
    revealAnswer() {
      this.showAnswer = true;
    },
    setScore(score) {
      this.userScore = score;
    },
    async submitReviewHandler() {
      if (this.userScore === null || this.userScore < 0 || this.userScore > 1) {
        this.errorMessage = "Please enter a score between 0.0 and 1.0.";
        return;
      }
      this.isSubmitting = true;
      this.errorMessage = '';
      try {
        await ApiService.submitCardReview(
          this.currentCard.card_id,
          this.userScore,
          this.userComment,
          this.typedInput
        );
        await this.fetchNextCard();
      } catch (error) {
        console.error("Error submitting review:", error);
        this.errorMessage = 'Failed to submit your review. Please try again.';
      } finally {
        this.isSubmitting = false;
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    },
    getDaysUntilReview(dateString) {
      if (!dateString) return null;
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const reviewDate = new Date(dateString);
      reviewDate.setHours(0, 0, 0, 0);
      const diffTime = reviewDate - today;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays < 0) return 'overdue';
      if (diffDays === 0) return 'today';
      if (diffDays === 1) return 'tomorrow';
      return `in ${diffDays} days`;
    }
  },
  mounted() {
    this.fetchNextCard();
  },
};
</script>

<style scoped>
.flashcard-view {
  padding: 20px;
  max-width: 700px;
  margin: 0 auto;
  font-family: Arial, sans-serif;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.card-type-badge {
  background-color: #e0e0e0;
  color: #333;
  padding: 5px 10px;
  border-radius: 12px;
  font-size: 0.8em;
}

.card-csv-number {
  font-size: 0.9em;
  color: #777;
}

.loading-message, .no-cards-message, .all-done-message, .error-message {
  text-align: center;
  padding: 20px;
  background-color: #f0f0f0;
  border-radius: 8px;
  margin-top: 20px;
}

.error-message {
  color: red;
  background-color: #ffe0e0;
}

.central-error {
  margin-top: 20px;
  text-align: center;
  padding: 15px;
  border-radius: 8px;
}

.flashcard-container {
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 20px;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.sentence-display {
  font-size: 1.2em;
  color: #555;
  margin-bottom: 15px;
  line-height: 1.5;
}

.last-reviewed {
  font-size: 0.8em;
  color: #777;
  margin-bottom: 20px;
}

.action-button {
  background-color: #4CAF50;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
  margin-top: 10px;
  transition: background-color 0.3s;
}

.action-button:hover {
  background-color: #45a049;
}

.action-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.card-back {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.comments-section {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  padding: 10px;
  margin-top: 15px;
  border-radius: 4px;
  font-size: 0.9em;
}

.comments-section strong {
  display: block;
  margin-bottom: 5px;
}

.review-inputs {
  margin-top: 20px;
}

.review-inputs div {
  margin-bottom: 15px;
}

.review-inputs label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

.review-inputs input[type="number"],
.review-inputs textarea {
  width: calc(100% - 22px);
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
}

.review-inputs textarea {
  resize: vertical;
  min-height: 60px;
}

.score-quick-picks {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.score-button {
  background-color: #f0f0f0;
  color: #333;
  border: 2px solid #ccc;
  border-radius: 6px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 0.95em;
  font-weight: 500;
  transition: all 0.2s;
  min-width: 50px;
}

.score-button:hover {
  background-color: #e0e0e0;
  border-color: #999;
}

.score-button-active {
  background-color: #4CAF50;
  color: white;
  border-color: #4CAF50;
}

.score-button-active:hover {
  background-color: #45a049;
  border-color: #45a049;
}

.score-input {
  margin-top: 8px;
}

.card-stats {
  background-color: #f0f8ff;
  border: 1px solid #b3d9ff;
  border-radius: 6px;
  padding: 12px;
  margin-top: 15px;
  font-size: 0.9em;
}

.stat-item {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-item:last-child {
  margin-bottom: 0;
}

.stat-item strong {
  color: #333;
  min-width: 100px;
}

.status-learning {
  background-color: #ffc107;
  color: #000;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: bold;
}

.status-review {
  background-color: #28a745;
  color: white;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: bold;
}

.avg-score {
  color: #666;
  font-size: 0.9em;
  margin-left: 5px;
}

.days-until {
  color: #17a2b8;
  font-size: 0.9em;
  margin-left: 5px;
  font-weight: 500;
}

.ease-factor-info {
  position: relative;
}

.info-icon {
  cursor: help;
  margin-left: 5px;
  font-size: 0.9em;
  opacity: 0.7;
}

.ease-factor-info:hover .info-icon {
  opacity: 1;
}
</style>
