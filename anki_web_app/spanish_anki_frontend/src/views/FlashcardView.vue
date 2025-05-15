<template>
  <div class="flashcard-view">
    <h1>Flashcard Review</h1>

    <div v-if="isLoading" class="loading-message">
      <p>Loading next card...</p>
    </div>

    <div v-if="!isLoading && !currentCard && !allCardsDone" class="no-cards-message">
      <p>No cards due for review right now. Check back later!</p>
      <!-- Optionally, add a button to fetch statistics or go to dashboard -->
    </div>

    <div v-if="allCardsDone" class="all-done-message">
      <p>Congratulations! You've reviewed all available cards for now!</p>
    </div>

    <div v-if="!isLoading && currentCard" class="flashcard-container">
      <!-- Front of the Card -->
      <div class="card-front">
        <h2>{{ currentCard.key_spanish_word }}</h2>
        <p class="spanish-sentence">{{ currentCard.spanish_sentence_example }}</p>
        <p v-if="currentCard.last_reviewed_date" class="last-reviewed">
          Last reviewed: {{ formatDate(currentCard.last_reviewed_date) }}
        </p>
      </div>

      <!-- Answer Button -->
      <button v-if="!showAnswer" @click="revealAnswer" class="action-button">Show Answer</button>

      <!-- Back of the Card (shown after clicking "Show Answer") -->
      <div v-if="showAnswer" class="card-back">
        <hr>
        <p><strong>Key Word Translation:</strong> {{ currentCard.key_word_english_translation }}</p>
        <p><strong>Sentence Translation:</strong> {{ currentCard.english_sentence_example }}</p>
        
        <div v-if="currentCard.base_comment" class="comments-section">
          <strong>Base Comment:</strong>
          <p style="white-space: pre-wrap;">{{ currentCard.base_comment }}</p>
        </div>

        <div v-if="currentCard.ai_explanation" class="comments-section">
          <strong>AI Explanation:</strong>
          <p style="white-space: pre-wrap;">{{ currentCard.ai_explanation }}</p>
        </div>
        
        <div class="review-inputs">
          <div>
            <label for="userScore">Your Score (0.0 - 1.0):</label>
            <input type="number" id="userScore" v-model.number="userScore" min="0" max="1" step="0.1" />
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
      <div v-if="errorMessage" class="error-message">
        <p>{{ errorMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'FlashcardView',
  data() {
    return {
      currentCard: null,
      showAnswer: false,
      userScore: 1.0, // Default score
      userComment: '',
      isLoading: true,
      isSubmitting: false,
      allCardsDone: false, // Flag to indicate no more cards
      errorMessage: '',
    };
  },
  methods: {
    async fetchNextCard() {
      this.isLoading = true;
      this.errorMessage = '';
      this.allCardsDone = false;
      try {
        const response = await ApiService.getNextCard();
        if (response.status === 200 && response.data) {
          this.currentCard = response.data;
          this.showAnswer = false;
          this.userScore = 1.0; // Reset score for new card
          this.userComment = '';   // Reset comment
        } else if (response.status === 204) {
          this.currentCard = null;
          this.allCardsDone = true; // No more cards
        }
      } catch (error) {
        console.error("Error fetching next card:", error);
        this.errorMessage = 'Failed to load the next card. Please check your connection or try again later.';
        if (error.response && error.response.status === 204) {
            this.currentCard = null;
            this.allCardsDone = true;
        } else {
            this.currentCard = null; // Clear card on other errors too
        }
      } finally {
        this.isLoading = false;
      }
    },
    revealAnswer() {
      this.showAnswer = true;
    },
    async submitReviewHandler() {
      if (this.userScore === null || this.userScore < 0 || this.userScore > 1) {
        this.errorMessage = "Please enter a score between 0.0 and 1.0.";
        return;
      }
      this.isSubmitting = true;
      this.errorMessage = '';
      try {
        await ApiService.submitReview(
          this.currentCard.sentence_id, // Make sure your API returns sentence_id
          this.userScore,
          this.userComment
        );
        // Successfully submitted, fetch the next card
        await this.fetchNextCard();
      } catch (error) {
        console.error("Error submitting review:", error);
        this.errorMessage = 'Failed to submit your review. Please try again.';
        // Optionally, handle specific error responses
      } finally {
        this.isSubmitting = false;
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A';
      const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
      return new Date(dateString).toLocaleDateString(undefined, options);
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
  max-width: 600px;
  margin: 0 auto;
  font-family: Arial, sans-serif;
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

.flashcard-container {
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 20px;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card-front h2 {
  color: #333;
  margin-bottom: 5px;
}

.spanish-sentence {
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

.card-back p {
  margin-bottom: 10px;
  line-height: 1.4;
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
  width: calc(100% - 22px); /* Account for padding and border */
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
}

.review-inputs textarea {
  resize: vertical;
  min-height: 60px;
}
</style> 