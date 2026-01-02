<template>
  <div class="reader-view">
    <div class="header-actions">
      <h1>Reader</h1>
      <div class="action-buttons">
        <router-link to="/reader/import" class="btn btn-primary">Import Lesson</router-link>
        <router-link to="/reader" class="btn btn-secondary" v-if="lessonId">Back to Lessons</router-link>
      </div>
    </div>

    <div v-if="isLoading" class="loading-message">
      <p>Loading lesson...</p>
    </div>

    <div v-if="errorMessage" class="error-message">
      <p>{{ errorMessage }}</p>
    </div>

    <!-- Lesson List View -->
    <div v-if="!lessonId && !isLoading && !errorMessage" class="lessons-list">
      <h2>Your Lessons</h2>
      <div v-if="lessons.length === 0" class="empty-state">
        <p>No lessons yet. <router-link to="/reader/import">Import your first lesson</router-link></p>
      </div>
      <div v-else class="lessons-grid">
        <div 
          v-for="lesson in lessons" 
          :key="lesson.lesson_id" 
          class="lesson-card"
          @click="loadLesson(lesson.lesson_id)"
        >
          <h3>{{ lesson.title }}</h3>
          <p class="lesson-meta">
            <span>{{ (lesson.language || 'de').toUpperCase() }}</span>
            <span>{{ lesson.token_count || 0 }} tokens</span>
            <span>{{ formatDate(lesson.created_at) }}</span>
          </p>
          <p class="lesson-preview">{{ (lesson.text || '').substring(0, 150) }}{{ lesson.text && lesson.text.length > 150 ? '...' : '' }}</p>
        </div>
      </div>
    </div>

    <!-- Lesson Reader View -->
    <div v-if="lessonId && lesson && !isLoading" class="lesson-reader">
      <div class="lesson-header">
        <h2>{{ lesson.title }}</h2>
        <div class="lesson-controls">
          <button v-if="lesson.audio_url" @click="toggleAudio" class="btn btn-secondary">
            {{ isPlaying ? '⏸ Pause' : '▶ Play Audio' }}
          </button>
          <audio 
            ref="audioPlayer" 
            :src="lesson.audio_url" 
            @ended="isPlaying = false"
            style="display: none;"
          ></audio>
        </div>
      </div>

      <!-- Translation Popover -->
      <div v-if="selectedToken" class="token-popover" :style="popoverStyle">
        <div class="popover-content">
          <div class="popover-header">
            <strong>{{ selectedToken.text }}</strong>
            <button @click="closePopover" class="close-btn">×</button>
          </div>
          <div v-if="selectedToken.translation" class="popover-body">
            <p><strong>Translation:</strong> {{ selectedToken.translation }}</p>
            <p v-if="sentenceContext" class="sentence-context">
              <strong>Context:</strong> {{ sentenceContext }}
            </p>
            <p v-if="sentenceTranslation" class="sentence-translation">
              <strong>Sentence:</strong> {{ sentenceTranslation }}
            </p>
            <button 
              @click="addToFlashcards" 
              class="btn btn-primary"
              :disabled="selectedToken.added_to_flashcards"
            >
              {{ selectedToken.added_to_flashcards ? '✓ Added to Flashcards' : 'Add to Flashcards' }}
            </button>
          </div>
          <div v-else class="popover-loading">
            Loading translation...
          </div>
        </div>
      </div>

      <!-- Lesson Text with Tokens -->
      <div class="lesson-text-container">
        <div class="lesson-text" ref="lessonText">
          <template v-if="tokens && tokens.length > 0">
            <span
              v-for="token in tokens"
              :key="token.token_id"
              :class="getTokenClass(token)"
              @click="handleTokenClick(token, $event)"
              :data-token-id="token.token_id"
            >
              {{ token.text || '' }}
            </span>
          </template>
          <div v-else class="no-tokens-message">
            No tokens available. The lesson may not have been tokenized yet.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ApiService from '../services/ApiService'

export default {
  name: 'ReaderView',
  props: {
    id: {
      type: [String, Number],
      default: null
    }
  },
  data() {
    return {
      lessons: [],
      lesson: null,
      tokens: [],
      isLoading: false,
      errorMessage: null,
      lessonId: null,
      selectedToken: null,
      sentenceContext: null,
      sentenceTranslation: null,
      popoverStyle: {},
      isPlaying: false,
      audioPlayer: null
    }
  },
  mounted() {
    this.initializeLessonId()
  },
  watch: {
    '$route.params.id': {
      handler() {
        this.initializeLessonId()
      },
      immediate: false
    },
    id() {
      this.initializeLessonId()
    }
  },
  methods: {
    initializeLessonId() {
      // Check route params first, then props
      const routeId = this.$route?.params?.id
      const propId = this.id
      const idToUse = routeId || propId
      
      this.lessonId = idToUse ? parseInt(idToUse) : null
      
      if (this.lessonId) {
        this.loadLesson(this.lessonId)
      } else {
        this.loadLessons()
      }
    },
    async loadLessons() {
      this.isLoading = true
      this.errorMessage = null
      try {
        const response = await ApiService.reader.getLessons()
        // Handle paginated response or direct array
        if (response.data && Array.isArray(response.data)) {
          this.lessons = response.data
        } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
          this.lessons = response.data.results
        } else {
          this.lessons = []
        }
      } catch (error) {
        console.error('Error loading lessons:', error)
        this.errorMessage = error.response?.data?.error || error.response?.data?.detail || 'Failed to load lessons. Please try again.'
        this.lessons = []
      } finally {
        this.isLoading = false
      }
    },
    async loadLesson(lessonId) {
      this.lessonId = lessonId
      this.isLoading = true
      this.errorMessage = null
      this.selectedToken = null // Clear any selected token
      try {
        const response = await ApiService.reader.getLesson(lessonId)
        if (response.data) {
          this.lesson = response.data
          this.tokens = Array.isArray(response.data.tokens) ? response.data.tokens : []
        } else {
          throw new Error('Invalid response data')
        }
        // Navigate to lesson detail route if not already there
        if (this.$route && this.$route.name !== 'LessonDetail' && this.$router) {
          this.$router.push({ name: 'LessonDetail', params: { id: lessonId } }).catch(() => {
            // Ignore navigation errors (e.g., already on that route)
          })
        }
      } catch (error) {
        console.error('Error loading lesson:', error)
        this.errorMessage = error.response?.data?.error || error.response?.data?.detail || 'Failed to load lesson. Please try again.'
        this.lesson = null
        this.tokens = []
      } finally {
        this.isLoading = false
      }
    },
    async handleTokenClick(token, event) {
      if (!token || !event || !event.target) return
      
      // Close any existing popover
      if (this.selectedToken && this.selectedToken.token_id === token.token_id) {
        this.closePopover()
        return
      }

      // Position popover near clicked token
      try {
        const rect = event.target.getBoundingClientRect()
        this.popoverStyle = {
          position: 'fixed',
          top: `${rect.bottom + 10}px`,
          left: `${rect.left}px`,
          zIndex: 1000
        }
      } catch (e) {
        // Fallback positioning
        this.popoverStyle = {
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 1000
        }
      }

      this.selectedToken = { ...token } // Copy token to avoid reactivity issues
      this.sentenceContext = null
      this.sentenceTranslation = null

      try {
        const response = await ApiService.reader.clickToken(token.token_id)
        if (response.data) {
          if (response.data.token) {
            this.selectedToken = response.data.token
          }
          this.sentenceContext = response.data.sentence || null
          this.sentenceTranslation = response.data.sentence_translation || null
        }
      } catch (error) {
        console.error('Error clicking token:', error)
        // Still show popover with cached translation if available
        if (token.translation) {
          this.selectedToken = { ...token }
        }
      }
    },
    closePopover() {
      this.selectedToken = null
      this.sentenceContext = null
      this.sentenceTranslation = null
    },
    async addToFlashcards() {
      if (!this.selectedToken || !this.lesson) return

      try {
        await ApiService.reader.addToFlashcards({
          token_id: this.selectedToken.token_id,
          front: this.selectedToken.text,
          back: this.selectedToken.translation || '',
          sentence_context: this.sentenceContext || '',
          lesson_id: this.lesson.lesson_id
        })
        
        // Update token status
        this.selectedToken.added_to_flashcards = true
        // Update in tokens array
        const tokenIndex = this.tokens.findIndex(t => t.token_id === this.selectedToken.token_id)
        if (tokenIndex !== -1) {
          this.tokens[tokenIndex].added_to_flashcards = true
        }
        
        alert('Card added to flashcards successfully!')
      } catch (error) {
        console.error('Error adding to flashcards:', error)
        alert('Failed to add card to flashcards. Please try again.')
      }
    },
    getTokenClass(token) {
      if (!token) return 'token'
      const classes = ['token']
      if (token.added_to_flashcards) {
        classes.push('token-added')
      }
      if (token.clicked_count && token.clicked_count > 0) {
        classes.push('token-clicked')
      }
      return classes.join(' ')
    },
    toggleAudio() {
      const audioPlayer = this.$refs.audioPlayer
      if (!audioPlayer) return
      
      try {
        if (this.isPlaying) {
          audioPlayer.pause()
          this.isPlaying = false
        } else {
          audioPlayer.play().catch(error => {
            console.error('Error playing audio:', error)
            this.isPlaying = false
          })
          this.isPlaying = true
        }
      } catch (error) {
        console.error('Error toggling audio:', error)
        this.isPlaying = false
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      try {
        const date = new Date(dateString)
        if (isNaN(date.getTime())) return dateString
        return date.toLocaleDateString()
      } catch (e) {
        return dateString
      }
    }
  }
}
</script>

<style scoped>
.reader-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.header-actions h1 {
  margin: 0;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn:hover {
  opacity: 0.9;
}

.loading-message, .error-message {
  text-align: center;
  padding: 40px;
}

.error-message {
  color: #dc3545;
}

/* Lessons List */
.lessons-list {
  margin-top: 20px;
}

.lessons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.lesson-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.lesson-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.lesson-card h3 {
  margin: 0 0 10px 0;
}

.lesson-meta {
  font-size: 0.9em;
  color: #666;
  margin: 10px 0;
}

.lesson-meta span {
  margin-right: 15px;
}

.lesson-preview {
  color: #888;
  font-size: 0.9em;
  margin-top: 10px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* Lesson Reader */
.lesson-reader {
  margin-top: 20px;
}

.lesson-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #eee;
}

.lesson-controls {
  display: flex;
  gap: 10px;
}

.lesson-text-container {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 30px;
  margin-top: 20px;
  line-height: 2;
  font-size: 1.1em;
}

.lesson-text {
  max-width: 100%;
  word-wrap: break-word;
}

.token {
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
  transition: background-color 0.2s;
  display: inline-block;
  white-space: pre-wrap;
}

.token:hover {
  background-color: #e3f2fd;
}

.token-clicked {
  background-color: #bbdefb;
}

.token-added {
  background-color: #c8e6c9;
  font-weight: 500;
}

.token-added:hover {
  background-color: #a5d6a7;
}

/* Popover */
.token-popover {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 300px;
  max-width: 500px;
}

.popover-content {
  padding: 15px;
}

.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #000;
}

.popover-body p {
  margin: 10px 0;
}

.sentence-context, .sentence-translation {
  font-style: italic;
  color: #666;
  font-size: 0.9em;
}

.popover-loading {
  text-align: center;
  padding: 20px;
  color: #666;
}

.no-tokens-message {
  text-align: center;
  padding: 20px;
  color: #666;
  font-style: italic;
}
</style>
