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
      <div class="loading-spinner"></div>
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
        <div class="lesson-title-section">
          <h2>{{ lesson.title }}</h2>
          <div v-if="lesson.listening_time_formatted" class="listening-stats">
            <span class="listening-icon">🎧</span>
            <span>Listened: {{ lesson.listening_time_formatted }}</span>
          </div>
        </div>
        <div v-if="lesson.audio_url" class="audio-player-section">
          <div class="audio-controls">
            <button @click="toggleAudio" class="btn btn-audio" :class="{ 'playing': isPlaying }">
              <span v-if="isPlaying">⏸</span>
              <span v-else>▶</span>
            </button>
            <div class="audio-info">
              <div class="audio-time">
                <span>{{ formatTime(currentTime) }}</span>
                <span>/</span>
                <span>{{ formatTime(duration) }}</span>
              </div>
              <input 
                type="range" 
                min="0" 
                :max="duration || 0" 
                :value="currentTime"
                @input="seekAudio"
                class="audio-progress"
              />
            </div>
          </div>
          <audio 
            ref="audioPlayer" 
            :src="lesson.audio_url" 
            @loadedmetadata="onAudioLoaded"
            @timeupdate="onTimeUpdate"
            @ended="onAudioEnded"
            @play="isPlaying = true"
            @pause="isPlaying = false"
            style="display: none;"
          ></audio>
        </div>
        <div v-else class="no-audio-message">
          <small>No audio available.</small>
          <button @click="generateTTSForLesson" class="btn btn-primary btn-small" :disabled="isGeneratingTTS">
            {{ isGeneratingTTS ? 'Generating...' : 'Generate TTS Audio' }}
          </button>
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
            <div class="loading-spinner-small"></div>
            <p>Loading translation...</p>
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
      audioPlayer: null,
      currentTime: 0,
      duration: 0,
      listeningTimeInterval: null,
      lastListeningTime: 0,
      listeningTimeAccumulator: 0,
      isGeneratingTTS: false
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
          this.updateListeningTime()
        } else {
          // Reset tracking when starting playback
          this.lastListeningTime = audioPlayer.currentTime || 0
          audioPlayer.play().catch(error => {
            console.error('Error playing audio:', error)
            this.isPlaying = false
          })
        }
      } catch (error) {
        console.error('Error toggling audio:', error)
        this.isPlaying = false
      }
    },
    onAudioLoaded() {
      const audioPlayer = this.$refs.audioPlayer
      if (audioPlayer) {
        this.duration = audioPlayer.duration || 0
      }
    },
    onTimeUpdate() {
      const audioPlayer = this.$refs.audioPlayer
      if (audioPlayer && this.isPlaying) {
        this.currentTime = audioPlayer.currentTime || 0
        
        // Accumulate listening time
        const timeDelta = this.currentTime - this.lastListeningTime
        if (timeDelta > 0 && timeDelta < 10) { // Sanity check: no jumps > 10 seconds
          this.listeningTimeAccumulator += timeDelta
        }
        this.lastListeningTime = this.currentTime
        
        // Update listening time every 5 seconds
        if (this.listeningTimeAccumulator >= 5) {
          this.updateListeningTime()
        }
      }
    },
    onAudioEnded() {
      this.isPlaying = false
      this.currentTime = 0
      this.lastListeningTime = 0
      this.updateListeningTime()
    },
    seekAudio(event) {
      const audioPlayer = this.$refs.audioPlayer
      if (audioPlayer) {
        audioPlayer.currentTime = parseFloat(event.target.value)
        this.currentTime = audioPlayer.currentTime
      }
    },
    formatTime(seconds) {
      if (!seconds || isNaN(seconds)) return '0:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins}:${secs.toString().padStart(2, '0')}`
    },
    async updateListeningTime() {
      if (!this.lessonId || this.listeningTimeAccumulator < 1) return
      
      const secondsToUpdate = Math.floor(this.listeningTimeAccumulator)
      
      try {
        await ApiService.reader.updateListeningTime(this.lessonId, secondsToUpdate)
        this.listeningTimeAccumulator = 0 // Reset accumulator
        
        // Refresh lesson data to get updated listening time
        if (this.lessonId) {
          const response = await ApiService.reader.getLesson(this.lessonId)
          if (response.data) {
            this.lesson = response.data
          }
        }
      } catch (error) {
        console.error('Error updating listening time:', error)
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
    },
    async generateTTSForLesson() {
      if (!this.lessonId || !this.lesson) return
      
      this.isGeneratingTTS = true
      try {
        console.log('Generating TTS for lesson:', this.lessonId)
        const response = await ApiService.reader.generateTTS(this.lessonId)
        console.log('TTS Response:', response)
        
        if (response && response.data && response.data.audio_url) {
          // Reload lesson to get updated audio_url
          await this.loadLesson(this.lessonId)
          alert('TTS audio generated successfully!')
        } else {
          const errorMsg = response?.data?.error || 'Unknown error'
          alert(`TTS generation failed: ${errorMsg}`)
        }
      } catch (error) {
        console.error('TTS generation error:', error)
        const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Check console for details'
        alert(`TTS generation failed: ${errorMsg}`)
      } finally {
        this.isGeneratingTTS = false
      }
    }
  },
  beforeUnmount() {
    // Clean up listening time tracking
    if (this.listeningTimeInterval) {
      clearInterval(this.listeningTimeInterval)
    }
    this.updateListeningTime()
  }
}
</script>

<style scoped>
.reader-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .reader-view {
    padding: 15px;
  }
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

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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

@media (max-width: 768px) {
  .lessons-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
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
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #eee;
}

.lesson-title-section {
  margin-bottom: 20px;
}

.lesson-title-section h2 {
  margin: 0 0 10px 0;
}

.listening-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 0.9em;
}

.listening-icon {
  font-size: 1.2em;
}

.audio-player-section {
  margin-top: 15px;
}

.audio-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f5f5f5;
  border-radius: 8px;
}

@media (max-width: 768px) {
  .audio-controls {
    flex-direction: column;
    gap: 10px;
  }
  
  .audio-info {
    width: 100%;
  }
}

.btn-audio {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  padding: 0;
  transition: all 0.3s ease;
}

.btn-audio.playing {
  background-color: #28a745;
  color: white;
}

.btn-audio:hover {
  transform: scale(1.05);
}

.audio-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.audio-time {
  display: flex;
  gap: 5px;
  font-size: 0.9em;
  color: #666;
  font-variant-numeric: tabular-nums;
}

.audio-progress {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #ddd;
  outline: none;
  cursor: pointer;
  transition: background 0.3s;
}

.audio-progress:hover {
  background: #ccc;
}

.audio-progress::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
}

.audio-progress::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
  border: none;
}

.no-audio-message {
  margin-top: 15px;
  padding: 15px;
  background: #fff3cd;
  border-radius: 4px;
  color: #856404;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-small {
  padding: 6px 12px;
  font-size: 0.9em;
  margin-left: 10px;
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
  transition: all 0.2s ease;
  display: inline-block;
  white-space: pre-wrap;
  position: relative;
}

.token:hover {
  background-color: #e3f2fd;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.token-clicked {
  background-color: #bbdefb;
  animation: tokenClick 0.3s ease;
}

.token-added {
  background-color: #c8e6c9;
  font-weight: 500;
  border-bottom: 2px solid #4caf50;
}

.token-added:hover {
  background-color: #a5d6a7;
}

@keyframes tokenClick {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

/* Popover */
.token-popover {
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
  min-width: 300px;
  max-width: 500px;
  animation: popoverFadeIn 0.2s ease;
  z-index: 1000;
}

@media (max-width: 768px) {
  .token-popover {
    min-width: 250px;
    max-width: calc(100vw - 40px);
    left: 20px !important;
    right: 20px;
    transform: none !important;
  }
}

@keyframes popoverFadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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

.popover-loading p {
  margin-top: 10px;
  margin-bottom: 0;
}

.loading-spinner-small {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #007bff;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

.no-tokens-message {
  text-align: center;
  padding: 20px;
  color: #666;
  font-style: italic;
}
</style>
