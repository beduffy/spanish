<template>
  <div class="card-editor-view">
    <h1>{{ isEditMode ? 'Edit Card' : 'Create New Card' }}</h1>

    <div v-if="isLoading" class="loading-message">
      <p>Loading card...</p>
    </div>
    <div v-if="errorMessage" class="error-message">
      <p>{{ errorMessage }}</p>
    </div>

    <div v-if="!isLoading" class="editor-form">
      <form @submit.prevent="saveCard">
        <div class="form-group">
          <label for="front">Front (Prompt) *</label>
          <textarea id="front" v-model="cardData.front" rows="3" required></textarea>
        </div>

        <div class="form-group">
          <label for="back">Back (Answer) *</label>
          <textarea id="back" v-model="cardData.back" rows="3" required></textarea>
        </div>

        <div class="form-group">
          <label for="tags">Tags (comma-separated)</label>
          <input type="text" id="tags" v-model="tagsInput" placeholder="tag1, tag2, tag3" />
        </div>

        <div class="form-group">
          <label for="notes">Notes</label>
          <textarea id="notes" v-model="cardData.notes" rows="4"></textarea>
        </div>

        <div v-if="!isEditMode" class="form-group checkbox-group">
          <label>
            <input type="checkbox" v-model="createReverse" />
            Create reverse card (back → front)
          </label>
        </div>

        <div class="form-actions">
          <button type="submit" :disabled="isSaving" class="btn btn-primary">
            {{ isSaving ? 'Saving...' : (isEditMode ? 'Update Card' : 'Create Card') }}
          </button>
          <router-link to="/cards" class="btn btn-secondary">Cancel</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import ApiService from '@/services/ApiService';

export default {
  name: 'CardEditorView',
  props: {
    id: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      cardData: {
        front: '',
        back: '',
        tags: [],
        notes: ''
      },
      tagsInput: '',
      createReverse: true,
      isLoading: false,
      isSaving: false,
      errorMessage: '',
      isEditMode: false
    };
  },
  methods: {
    async loadCard() {
      if (!this.id) {
        this.isEditMode = false;
        this.isLoading = false;
        return;
      }

      this.isLoading = true;
      this.errorMessage = '';
      try {
        const response = await ApiService.getCardDetails(this.id);
        if (response.status === 200 && response.data) {
          this.cardData = {
            front: response.data.front || '',
            back: response.data.back || '',
            tags: response.data.tags || [],
            notes: response.data.notes || ''
          };
          this.tagsInput = this.cardData.tags.join(', ');
          this.isEditMode = true;
        }
      } catch (error) {
        console.error('Error loading card:', error);
        this.errorMessage = 'Failed to load card. It may not exist.';
      } finally {
        this.isLoading = false;
      }
    },
    async saveCard() {
      if (!this.cardData.front.trim() || !this.cardData.back.trim()) {
        this.errorMessage = 'Front and Back are required.';
        return;
      }

      this.isSaving = true;
      this.errorMessage = '';

      // Parse tags
      const tags = this.tagsInput.split(',').map(t => t.trim()).filter(t => t.length > 0);

      const payload = {
        front: this.cardData.front.trim(),
        back: this.cardData.back.trim(),
        tags: tags,
        notes: this.cardData.notes.trim()
      };

      try {
        if (this.isEditMode) {
          await ApiService.updateCard(this.id, payload);
        } else {
          await ApiService.createCard({
            ...payload,
            create_reverse: this.createReverse
          });
        }
        this.$router.push('/cards');
      } catch (error) {
        console.error('Error saving card:', error);
        this.errorMessage = error.response?.data?.error || 'Failed to save card. Please try again.';
      } finally {
        this.isSaving = false;
      }
    }
  },
  mounted() {
    this.loadCard();
  }
};
</script>

<style scoped>
.card-editor-view {
  padding: 20px;
  font-family: Arial, sans-serif;
  max-width: 800px;
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

.editor-form {
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.form-group {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #333;
}

input[type="text"],
textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
  font-family: inherit;
}

textarea {
  resize: vertical;
  min-height: 80px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  font-weight: normal;
}

.checkbox-group input[type="checkbox"] {
  width: auto;
  margin-right: 8px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.btn {
  padding: 10px 20px;
  border-radius: 4px;
  text-decoration: none;
  font-weight: bold;
  border: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-primary:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #545b62;
}
</style>
