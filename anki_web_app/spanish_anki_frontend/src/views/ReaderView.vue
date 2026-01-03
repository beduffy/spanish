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
        >
          <div class="lesson-card-content" @click="loadLesson(lesson.lesson_id)">
            <h3>{{ lesson.title }}</h3>
            <p class="lesson-meta">
              <span>{{ (lesson.language || 'de').toUpperCase() }}</span>
              <span>{{ lesson.token_count || 0 }} tokens</span>
              <span>{{ formatDate(lesson.created_at) }}</span>
              <span class="status-badge" :class="`status-${lesson.status || 'not_started'}`">
                {{ getStatusLabel(lesson.status || 'not_started') }}
              </span>
            </p>
            <div v-if="lesson.progress_percentage !== undefined" class="progress-bar-container">
              <div class="progress-bar" :style="{ width: `${lesson.progress_percentage}%` }"></div>
              <span class="progress-text">{{ lesson.progress_percentage }}%</span>
            </div>
            <p class="lesson-preview">{{ (lesson.text || '').substring(0, 150) }}{{ lesson.text && lesson.text.length > 150 ? '...' : '' }}</p>
            <div v-if="lesson.reading_time_formatted" class="lesson-reading-time">
              <small>Reading time: {{ lesson.reading_time_formatted }}</small>
            </div>
          </div>
          <div class="lesson-card-actions">
            <button @click.stop="editLesson(lesson)" class="btn btn-edit" title="Edit lesson">
              ✏️
            </button>
            <button @click.stop="confirmDeleteLesson(lesson)" class="btn btn-delete" title="Delete lesson">
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Lesson Reader View -->
    <div v-if="lessonId && lesson && !isLoading" class="lesson-reader">
      <div class="lesson-header">
        <div class="lesson-title-section">
          <h2>{{ lesson.title }}</h2>
          <div class="lesson-stats">
            <div v-if="lesson.listening_time_formatted" class="listening-stats">
              <span class="listening-icon">🎧</span>
              <span>Listened: {{ lesson.listening_time_formatted }}</span>
            </div>
            <div v-if="lesson.reading_time_formatted" class="reading-stats">
              <span class="reading-icon">📖</span>
              <span>Read: {{ lesson.reading_time_formatted }}</span>
            </div>
            <div v-if="lesson.progress_percentage !== undefined" class="progress-stats">
              <span class="progress-icon">📊</span>
              <span>{{ lesson.progress_percentage }}% complete</span>
              <span class="status-badge" :class="`status-${lesson.status}`">
                {{ getStatusLabel(lesson.status) }}
              </span>
            </div>
          </div>
        </div>
        <div class="lesson-actions">
          <button @click="editLesson(lesson)" class="btn btn-edit" title="Edit lesson">
            ✏️ Edit
          </button>
          <button @click="confirmDeleteLesson(lesson)" class="btn btn-delete" title="Delete lesson">
            🗑️ Delete
          </button>
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
            :src="getAudioUrl(lesson.audio_url)" 
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
      <div v-if="selectedToken || selectedPhrase" class="token-popover" :style="popoverStyle">
        <div class="popover-content">
          <div class="popover-header">
            <strong>{{ (selectedToken || selectedPhrase)?.text }}</strong>
            <button @click="closePopover" class="close-btn">×</button>
          </div>
          <div v-if="(selectedToken || selectedPhrase)?.translation || currentDictionaryEntry" class="popover-body">
            <!-- Dictionary Entry Section -->
            <div v-if="currentDictionaryEntry" class="dictionary-section">
              <div v-for="(meaning, index) in currentDictionaryEntry.meanings" :key="index" class="meaning-item">
                <div v-if="meaning.part_of_speech" class="part-of-speech">
                  <span class="pos-tag">{{ meaning.part_of_speech }}</span>
                </div>
                <ul class="definitions-list">
                  <li v-for="(definition, defIndex) in meaning.definitions" :key="defIndex" class="definition-item">
                    {{ definition }}
                  </li>
                </ul>
                <div v-if="meaning.examples && meaning.examples.length > 0" class="examples-section">
                  <strong class="examples-label">Examples:</strong>
                  <ul class="examples-list">
                    <li v-for="(example, exIndex) in meaning.examples" :key="exIndex" class="example-item">
                      <em>{{ example }}</em>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
            
            <!-- Fallback Translation (if no dictionary entry) -->
            <div v-if="!currentDictionaryEntry && (selectedToken || selectedPhrase)?.translation" class="translation-section">
              <p><strong>Translation:</strong> {{ (selectedToken || selectedPhrase).translation }}</p>
            </div>
            
            <!-- Sentence Context -->
            <div v-if="sentenceContext" class="sentence-context-section">
              <p class="sentence-context">
                <strong>Context:</strong> {{ sentenceContext }}
              </p>
            </div>
            <div v-if="sentenceTranslation" class="sentence-translation-section">
              <p class="sentence-translation">
                <strong>Sentence:</strong> {{ sentenceTranslation }}
              </p>
            </div>
            
            <!-- Known/Unknown Status Buttons (only for tokens, not phrases) -->
            <div v-if="selectedToken && !selectedPhrase" class="popover-status-actions">
              <div class="status-buttons">
                <button 
                  @click="markTokenAsKnown"
                  class="btn btn-status"
                  :class="{ 'btn-status-active': selectedToken?.status === 'known' }"
                  :disabled="isUpdatingStatus"
                >
                  {{ selectedToken?.status === 'known' ? '✓ Known' : 'Mark as Known' }}
                </button>
                <button 
                  @click="markTokenAsUnknown"
                  class="btn btn-status"
                  :class="{ 'btn-status-active': selectedToken?.status === 'unknown' }"
                  :disabled="isUpdatingStatus"
                >
                  {{ selectedToken?.status === 'unknown' ? '✗ Unknown' : 'Mark as Unknown' }}
                </button>
                <button 
                  v-if="selectedToken?.status"
                  @click="removeTokenStatus"
                  class="btn btn-status btn-status-clear"
                  :disabled="isUpdatingStatus"
                >
                  Clear Status
                </button>
              </div>
            </div>
            
            <!-- Add to Flashcards Button -->
            <div class="popover-actions">
              <button 
                @click="addToFlashcards" 
                class="btn btn-primary"
                :disabled="(selectedToken || selectedPhrase)?.added_to_flashcards"
              >
                {{ (selectedToken || selectedPhrase)?.added_to_flashcards ? '✓ Added to Flashcards' : 'Add to Flashcards' }}
              </button>
            </div>
          </div>
          <div v-else class="popover-loading">
            <div class="loading-spinner-small"></div>
            <p>Loading translation...</p>
          </div>
        </div>
      </div>

      <!-- Lesson Text with Tokens -->
      <div class="lesson-text-container">
        <div 
          class="lesson-text" 
          ref="lessonText"
          @mouseup="handleTextSelection"
          @selectstart="onSelectStart"
        >
          <template v-if="tokens && tokens.length > 0">
            <template v-for="(token, index) in tokens" :key="token.token_id">
              <span
                :class="getTokenClass(token)"
                @click="handleTokenClick(token, $event)"
                :data-token-id="token.token_id"
                :data-start-offset="token.start_offset"
                :data-end-offset="token.end_offset"
              >
                {{ token.text || '' }}
              </span>
              <span v-if="index < tokens.length - 1 && getTokenSpacing(token, tokens[index + 1])" class="token-spacing">
                {{ getTokenSpacing(token, tokens[index + 1]) }}
              </span>
            </template>
          </template>
          <div v-else class="no-tokens-message">
            No tokens available. The lesson may not have been tokenized yet.
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div v-if="toastMessage" class="toast" :class="`toast-${toastType}`">
      {{ toastMessage }}
    </div>

    <!-- Edit Lesson Modal -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Edit Lesson</h2>
          <button @click="closeEditModal" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div v-if="editError" class="error-message">
            {{ editError }}
          </div>
          <form @submit.prevent="saveLesson">
            <div class="form-group">
              <label for="edit-title">Title</label>
              <input 
                id="edit-title"
                v-model="editingLesson.title" 
                type="text" 
                required 
                class="form-control"
                placeholder="Lesson title"
              />
            </div>
            <div class="form-group">
              <label for="edit-language">Language</label>
              <select 
                id="edit-language"
                v-model="editingLesson.language" 
                class="form-control"
                required
              >
                <option value="es">Spanish (es)</option>
                <option value="de">German (de)</option>
                <option value="fr">French (fr)</option>
                <option value="it">Italian (it)</option>
                <option value="pt">Portuguese (pt)</option>
              </select>
            </div>
            <div class="form-group">
              <label for="edit-text">Text</label>
              <textarea 
                id="edit-text"
                v-model="editingLesson.text" 
                rows="10" 
                required 
                class="form-control"
                placeholder="Lesson text content"
              ></textarea>
            </div>
            <div class="form-group">
              <label for="edit-audio-url">Audio URL (optional)</label>
              <input 
                id="edit-audio-url"
                v-model="editingLesson.audio_url" 
                type="url" 
                class="form-control"
                placeholder="https://..."
              />
            </div>
            <div class="form-group">
              <label for="edit-source-type">Source Type</label>
              <select 
                id="edit-source-type"
                v-model="editingLesson.source_type" 
                class="form-control"
              >
                <option value="text">Text Paste</option>
                <option value="youtube">YouTube</option>
                <option value="url">URL</option>
                <option value="file">File Upload</option>
              </select>
            </div>
            <div class="form-group">
              <label for="edit-source-url">Source URL (optional)</label>
              <input 
                id="edit-source-url"
                v-model="editingLesson.source_url" 
                type="url" 
                class="form-control"
                placeholder="https://..."
              />
            </div>
            <div class="form-actions">
              <button type="button" @click="closeEditModal" class="btn btn-secondary">
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="isSaving">
                {{ isSaving ? 'Saving...' : 'Save Changes' }}
              </button>
            </div>
          </form>
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
      phrases: [],
      isLoading: false,
      errorMessage: null,
      lessonId: null,
      selectedToken: null,
      selectedPhrase: null,
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
      isGeneratingTTS: false,
      selectionStart: null,
      selectionEnd: null,
      toastMessage: null,
      toastTimeout: null,
      toastType: 'success',
      showEditModal: false,
      editingLesson: null,
      isSaving: false,
      editError: null,
      isUpdatingStatus: false,
      // Reading progress tracking
      readingTimeInterval: null,
      readingStartTime: null,
      lastProgressUpdate: null,
      wordsReadThisSession: new Set(),
      progressUpdateInterval: null,
      // Computed dictionary entry for current selection
      currentDictionaryEntry: null
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
    },
    selectedToken() {
      this.updateCurrentDictionaryEntry()
    },
    selectedPhrase() {
      this.updateCurrentDictionaryEntry()
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
      // Stop tracking for previous lesson
      this.stopReadingProgressTracking()
      
      this.lessonId = lessonId
      this.isLoading = true
      this.errorMessage = null
      this.selectedToken = null // Clear any selected token
      try {
        const response = await ApiService.reader.getLesson(lessonId)
        if (response.data) {
          this.lesson = response.data
          this.tokens = Array.isArray(response.data.tokens) ? response.data.tokens : []
          this.phrases = Array.isArray(response.data.phrases) ? response.data.phrases : []
          
          // Start tracking reading progress for this lesson
          this.startReadingProgressTracking()
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
      
      // Don't handle click if there's an active text selection
      const selection = window.getSelection()
      if (selection && selection.toString().trim().length > 0) {
        return
      }
      
      // Track word read
      this.trackWordRead(token.token_id)
      
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
      this.selectedPhrase = null // Clear phrase selection
      this.sentenceContext = null
      this.sentenceTranslation = null
      this.updateCurrentDictionaryEntry()

      try {
        const response = await ApiService.reader.clickToken(token.token_id)
        if (response.data) {
          if (response.data.token) {
            this.selectedToken = response.data.token
            // Debug: log dictionary entry
            if (response.data.token.dictionary_entry) {
              console.log('Dictionary entry received:', response.data.token.dictionary_entry)
            }
            this.updateCurrentDictionaryEntry()
          }
          this.sentenceContext = response.data.sentence || null
          this.sentenceTranslation = response.data.sentence_translation || null
        }
      } catch (error) {
        console.error('Error clicking token:', error)
        // Still show popover with cached translation if available
        if (token.translation) {
          this.selectedToken = { ...token }
          this.updateCurrentDictionaryEntry()
        }
      }
    },
    closePopover() {
      this.selectedToken = null
      this.selectedPhrase = null
      this.sentenceContext = null
      this.sentenceTranslation = null
      this.currentDictionaryEntry = null
    },
    getDictionaryEntry(item) {
      if (!item) return null
      if (item.dictionary_entry && item.dictionary_entry.meanings && item.dictionary_entry.meanings.length > 0) {
        return item.dictionary_entry
      }
      return null
    },
    updateCurrentDictionaryEntry() {
      const item = this.selectedToken || this.selectedPhrase
      this.currentDictionaryEntry = this.getDictionaryEntry(item)
    },
    async addToFlashcards() {
      if ((!this.selectedToken && !this.selectedPhrase) || !this.lesson) return

      const item = this.selectedToken || this.selectedPhrase
      const isPhrase = !!this.selectedPhrase

      try {
        await ApiService.reader.addToFlashcards({
          token_id: isPhrase ? undefined : this.selectedToken.token_id,
          phrase_id: isPhrase ? this.selectedPhrase.phrase_id : undefined,
          front: item.text,
          back: item.translation || '',
          sentence_context: this.sentenceContext || '',
          lesson_id: this.lesson.lesson_id
        })
        
        // Update status
        if (isPhrase) {
          this.selectedPhrase.added_to_flashcards = true
          const phraseIndex = this.phrases.findIndex(p => p.phrase_id === this.selectedPhrase.phrase_id)
          if (phraseIndex !== -1) {
            this.phrases[phraseIndex].added_to_flashcards = true
          }
        } else {
          this.selectedToken.added_to_flashcards = true
          const tokenIndex = this.tokens.findIndex(t => t.token_id === this.selectedToken.token_id)
          if (tokenIndex !== -1) {
            this.tokens[tokenIndex].added_to_flashcards = true
          }
        }
        
        const itemText = item.text || 'item'
        this.showToast(`✓ Added "${itemText}" to flashcards`, 'success')
      } catch (error) {
        console.error('Error adding to flashcards:', error)
        this.showToast('Failed to add card to flashcards. Please try again.', 'error')
      }
    },
    getTokenClass(token) {
      if (!token) return 'token'
      const classes = ['token']
      
      // Check if token is part of a phrase
      // Phrases have token_start_id and token_end_id which are token IDs
      const isInPhrase = this.phrases.some(phrase => {
        const tokenStartId = phrase.token_start_id || phrase.token_start
        const tokenEndId = phrase.token_end_id || phrase.token_end
        if (!tokenStartId || !tokenEndId) return false
        // Check if this token is between start and end tokens
        const startToken = this.tokens.find(t => t.token_id === tokenStartId)
        const endToken = this.tokens.find(t => t.token_id === tokenEndId)
        if (!startToken || !endToken) return false
        
        // Token is in phrase if its offsets are within the phrase range
        return token.start_offset >= startToken.start_offset && 
               token.end_offset <= endToken.end_offset
      })
      
      if (isInPhrase) {
        classes.push('token-in-phrase')
      }
      
      if (token.added_to_flashcards) {
        classes.push('token-added')
      }
      if (token.clicked_count && token.clicked_count > 0) {
        classes.push('token-clicked')
      }
      
      // Add status-based classes for known/unknown highlighting
      if (token.status === 'known') {
        classes.push('token-known')
      } else if (token.status === 'unknown') {
        classes.push('token-unknown')
      }
      return classes.join(' ')
    },
    async markTokenAsKnown() {
      if (!this.selectedToken || this.isUpdatingStatus) return
      
      this.isUpdatingStatus = true
      try {
        await ApiService.reader.updateTokenStatus(this.selectedToken.token_id, 'known')
        
        // Update the token status in the local state
        this.selectedToken.status = 'known'
        const tokenIndex = this.tokens.findIndex(t => t.token_id === this.selectedToken.token_id)
        if (tokenIndex !== -1) {
          this.tokens[tokenIndex].status = 'known'
        }
        
        this.showToast('Word marked as known', 'success')
      } catch (error) {
        console.error('Error marking token as known:', error)
        this.showToast('Failed to update status', 'error')
      } finally {
        this.isUpdatingStatus = false
      }
    },
    async markTokenAsUnknown() {
      if (!this.selectedToken || this.isUpdatingStatus) return
      
      this.isUpdatingStatus = true
      try {
        await ApiService.reader.updateTokenStatus(this.selectedToken.token_id, 'unknown')
        
        // Update the token status in the local state
        this.selectedToken.status = 'unknown'
        const tokenIndex = this.tokens.findIndex(t => t.token_id === this.selectedToken.token_id)
        if (tokenIndex !== -1) {
          this.tokens[tokenIndex].status = 'unknown'
        }
        
        this.showToast('Word marked as unknown', 'success')
      } catch (error) {
        console.error('Error marking token as unknown:', error)
        this.showToast('Failed to update status', 'error')
      } finally {
        this.isUpdatingStatus = false
      }
    },
    async removeTokenStatus() {
      if (!this.selectedToken || this.isUpdatingStatus) return
      
      this.isUpdatingStatus = true
      try {
        await ApiService.reader.removeTokenStatus(this.selectedToken.token_id)
        
        // Update the token status in the local state
        this.selectedToken.status = null
        const tokenIndex = this.tokens.findIndex(t => t.token_id === this.selectedToken.token_id)
        if (tokenIndex !== -1) {
          this.tokens[tokenIndex].status = null
        }
        
        this.showToast('Status cleared', 'success')
      } catch (error) {
        console.error('Error removing token status:', error)
        this.showToast('Failed to clear status', 'error')
      } finally {
        this.isUpdatingStatus = false
      }
    },
    onSelectStart() {
      // Allow text selection
      return true
    },
    async handleTextSelection() {
      // Small delay to ensure selection is complete
      setTimeout(() => {
        const selection = window.getSelection()
        if (!selection || selection.rangeCount === 0) {
          return
        }
        
        const range = selection.getRangeAt(0)
        const selectedText = selection.toString().trim()
        
        // Only create phrase if there's actual text selected (more than one word)
        if (!selectedText || selectedText.length < 2) {
          return
        }
        
        // Check if selection is within lesson text
        const lessonTextElement = this.$refs.lessonText
        if (!lessonTextElement || !lessonTextElement.contains(range.commonAncestorContainer)) {
          return
        }
        
        // Find tokens that are selected by checking which token elements are in the range
        const selectedTokens = []
        const tokenElements = lessonTextElement.querySelectorAll('[data-token-id]')
        
        tokenElements.forEach(element => {
          const tokenId = parseInt(element.getAttribute('data-token-id'))
          const token = this.tokens.find(t => t.token_id === tokenId)
          
          if (token && range.intersectsNode(element)) {
            selectedTokens.push(token)
          }
        })
        
        if (selectedTokens.length < 2) {
          // Single token or no tokens - let normal click handler deal with it
          return
        }
        
        // Sort tokens by offset
        selectedTokens.sort((a, b) => a.start_offset - b.start_offset)
        
        const startOffset = selectedTokens[0].start_offset
        const endOffset = selectedTokens[selectedTokens.length - 1].end_offset
        
        // Create phrase
        this.createPhraseFromSelection(startOffset, endOffset, range)
      }, 50)
    },
    async createPhraseFromSelection(startOffset, endOffset, range) {
      try {
        const response = await ApiService.reader.createPhrase(
          this.lessonId,
          startOffset,
          endOffset
        )
        
        if (response.data && response.data.phrase) {
          const newPhrase = response.data.phrase
          // Check if phrase already exists
          const existingIndex = this.phrases.findIndex(p => p.phrase_id === newPhrase.phrase_id)
          if (existingIndex === -1) {
            this.phrases.push(newPhrase)
          } else {
            this.phrases[existingIndex] = newPhrase
          }
          
          // Show popover for phrase
          this.selectedPhrase = newPhrase
          this.selectedToken = null
          
          // Get sentence context
          const sentenceText = this.getSentenceContext(startOffset)
          this.sentenceContext = sentenceText
          
          // Position popover
          const rect = range.getBoundingClientRect()
          this.popoverStyle = {
            position: 'fixed',
            top: `${rect.bottom + 10}px`,
            left: `${rect.left}px`,
            zIndex: 1000
          }
          
          // Get sentence translation if available
          if (this.lesson && sentenceText && this.lesson.sentence_translations) {
            this.sentenceTranslation = this.lesson.sentence_translations[sentenceText] || null
          }
          
          // Clear selection
          window.getSelection().removeAllRanges()
        }
      } catch (error) {
        console.error('Error creating phrase:', error)
        // If phrase already exists (200 status), show it
        if (error.response?.status === 200 && error.response?.data?.phrase) {
          const existingPhrase = error.response.data.phrase
          const existingIndex = this.phrases.findIndex(p => p.phrase_id === existingPhrase.phrase_id)
          if (existingIndex === -1) {
            this.phrases.push(existingPhrase)
          } else {
            this.phrases[existingIndex] = existingPhrase
          }
          this.selectedPhrase = existingPhrase
          this.selectedToken = null
          
          // Position popover
          const rect = range.getBoundingClientRect()
          this.popoverStyle = {
            position: 'fixed',
            top: `${rect.bottom + 10}px`,
            left: `${rect.left}px`,
            zIndex: 1000
          }
        }
      }
    },
    getSentenceContext(offset) {
      if (!this.lesson || !this.lesson.text) return ''
      
      const text = this.lesson.text
      const sentenceEnd = text.indexOf('.', offset)
      const sentenceStart = text.lastIndexOf('.', offset) + 1
      
      const start = sentenceStart === 0 ? 0 : sentenceStart
      const end = sentenceEnd === -1 ? text.length : sentenceEnd + 1
      
      return text.substring(start, end).trim()
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
    getAudioUrl(audioUrl) {
      if (!audioUrl) return ''
      // If already absolute URL, return as-is
      if (audioUrl.startsWith('http://') || audioUrl.startsWith('https://')) {
        return audioUrl
      }
      // In development, use backend URL directly
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return `http://localhost:8000${audioUrl}`
      }
      // In production, use relative URL (will be proxied or served by nginx)
      return audioUrl
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
          this.showToast('TTS audio generated successfully!', 'success')
        } else {
          const errorMsg = response?.data?.error || 'Unknown error'
          this.showToast(`TTS generation failed: ${errorMsg}`, 'error')
        }
      } catch (error) {
        console.error('TTS generation error:', error)
        const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Check console for details'
        this.showToast(`TTS generation failed: ${errorMsg}`, 'error')
      } finally {
        this.isGeneratingTTS = false
      }
    },
    editLesson(lesson) {
      this.editingLesson = {
        lesson_id: lesson.lesson_id,
        title: lesson.title || '',
        text: lesson.text || '',
        language: lesson.language || 'de',
        audio_url: lesson.audio_url || '',
        source_type: lesson.source_type || 'text',
        source_url: lesson.source_url || ''
      }
      this.editError = null
      this.showEditModal = true
    },
    closeEditModal() {
      this.showEditModal = false
      this.editingLesson = null
      this.editError = null
      this.isSaving = false
    },
    async saveLesson() {
      if (!this.editingLesson || !this.editingLesson.lesson_id) return
      
      this.isSaving = true
      this.editError = null
      
      try {
        const lessonData = {
          title: this.editingLesson.title,
          text: this.editingLesson.text,
          language: this.editingLesson.language,
          audio_url: this.editingLesson.audio_url || null,
          source_type: this.editingLesson.source_type,
          source_url: this.editingLesson.source_url || null
        }
        
        await ApiService.reader.updateLesson(this.editingLesson.lesson_id, lessonData)
        
        // Reload lessons list or current lesson
        if (this.lessonId === this.editingLesson.lesson_id) {
          await this.loadLesson(this.lessonId)
        } else {
          await this.loadLessons()
        }
        
        this.closeEditModal()
        this.showToast('Lesson updated successfully!', 'success')
      } catch (error) {
        console.error('Error updating lesson:', error)
        this.editError = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to update lesson. Please try again.'
      } finally {
        this.isSaving = false
      }
    },
    getTokenSpacing(currentToken, nextToken) {
      if (!currentToken || !nextToken || !this.lesson) return ''
      // Calculate spacing based on offsets in original text
      const gap = nextToken.start_offset - currentToken.end_offset
      if (gap <= 0) return ''
      // Extract the spacing from the original lesson text
      let spacing = this.lesson.text.substring(currentToken.end_offset, nextToken.start_offset)
      
      // Remove spaces before punctuation (common formatting issue)
      // Punctuation should not have spaces before it
      const nextIsPunctuation = /^[^\w\s]/.test(nextToken.text || '')
      if (nextIsPunctuation) {
        // Remove all leading spaces before punctuation
        spacing = spacing.replace(/^\s+/, '')
      }
      
      // Remove trailing spaces after punctuation (but keep one space after sentence-ending punctuation)
      const currentIsPunctuation = /^[^\w\s]/.test(currentToken.text || '')
      if (currentIsPunctuation) {
        // After punctuation like . ! ? : ; , keep only one space (or none if next is punctuation)
        if (nextIsPunctuation) {
          spacing = spacing.replace(/\s+$/, '')
        } else {
          // Normalize multiple spaces to single space
          spacing = spacing.replace(/\s+$/, ' ')
        }
      }
      
      return spacing
    },
    showToast(message, type = 'success') {
      this.toastMessage = message
      this.toastType = type
      
      // Clear existing timeout
      if (this.toastTimeout) {
        clearTimeout(this.toastTimeout)
      }
      
      // Auto-hide after 3 seconds
      this.toastTimeout = setTimeout(() => {
        this.toastMessage = null
        this.toastTimeout = null
      }, 3000)
    },
    confirmDeleteLesson(lesson) {
      if (confirm(`Are you sure you want to delete "${lesson.title}"? This action cannot be undone.`)) {
        this.deleteLesson(lesson.lesson_id)
      }
    },
    async deleteLesson(lessonId) {
      try {
        await ApiService.reader.deleteLesson(lessonId)
        
        // If we're viewing the deleted lesson, go back to list
        if (this.lessonId === lessonId) {
          this.lessonId = null
          this.lesson = null
          this.tokens = []
          this.phrases = []
          if (this.$router) {
            this.$router.push({ name: 'Reader' }).catch(() => {})
          }
        }
        
        // Reload lessons list
        await this.loadLessons()
        this.showToast('Lesson deleted successfully!', 'success')
      } catch (error) {
        console.error('Error deleting lesson:', error)
        const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to delete lesson. Please try again.'
        this.showToast(`Failed to delete lesson: ${errorMsg}`, 'error')
      }
    },
    getStatusLabel(status) {
      const labels = {
        'not_started': 'Not Started',
        'in_progress': 'In Progress',
        'completed': 'Completed'
      }
      return labels[status] || status
    },
    startReadingProgressTracking() {
      if (!this.lessonId) return
      
      // Reset session tracking
      this.wordsReadThisSession = new Set()
      this.readingStartTime = Date.now()
      this.lastProgressUpdate = Date.now()
      
      // Start reading time interval (update every 10 seconds)
      this.readingTimeInterval = setInterval(() => {
        this.updateReadingProgress()
      }, 10000)
      
      // Initial progress update to mark as in_progress if not started
      if (this.lesson && this.lesson.status === 'not_started') {
        this.updateReadingProgress({ status: 'in_progress' })
      }
    },
    stopReadingProgressTracking() {
      // Stop intervals
      if (this.readingTimeInterval) {
        clearInterval(this.readingTimeInterval)
        this.readingTimeInterval = null
      }
      if (this.progressUpdateInterval) {
        clearInterval(this.progressUpdateInterval)
        this.progressUpdateInterval = null
      }
      
      // Final progress update
      if (this.lessonId) {
        this.updateReadingProgress()
      }
      
      // Reset tracking
      this.wordsReadThisSession = new Set()
      this.readingStartTime = null
      this.lastProgressUpdate = null
    },
    trackWordRead(tokenId) {
      if (!this.lessonId || !tokenId) return
      
      // Track unique words read this session
      if (!this.wordsReadThisSession.has(tokenId)) {
        this.wordsReadThisSession.add(tokenId)
        // Update progress immediately
        this.updateReadingProgress({ words_read_delta: 1 })
      }
    },
    async updateReadingProgress(additionalData = {}) {
      if (!this.lessonId || this.isUpdatingStatus) return
      
      try {
        this.isUpdatingStatus = true
        
        const progressData = { ...additionalData }
        
        // Calculate reading time delta
        if (this.readingStartTime && this.lastProgressUpdate) {
          const now = Date.now()
          const secondsElapsed = Math.floor((now - this.lastProgressUpdate) / 1000)
          if (secondsElapsed > 0) {
            progressData.reading_time_seconds_delta = secondsElapsed
            this.lastProgressUpdate = now
          }
        }
        
        // Only update if there's something to update
        if (Object.keys(progressData).length > 0) {
          const response = await ApiService.reader.updateReadingProgress(this.lessonId, progressData)
          
          // Update local lesson data
          if (response.data && this.lesson) {
            Object.assign(this.lesson, {
              status: response.data.status,
              words_read: response.data.words_read,
              reading_time_seconds: response.data.reading_time_seconds,
              reading_time_formatted: response.data.reading_time_formatted,
              progress_percentage: response.data.progress_percentage,
              last_read_at: response.data.last_read_at,
              completed_at: response.data.completed_at
            })
          }
        }
      } catch (error) {
        console.error('Error updating reading progress:', error)
        // Don't show error toast for progress updates to avoid spam
      } finally {
        this.isUpdatingStatus = false
      }
    }
  },
  beforeUnmount() {
    // Clean up listening time tracking
    if (this.listeningTimeInterval) {
      clearInterval(this.listeningTimeInterval)
    }
    this.updateListeningTime()
    
    // Clean up reading progress tracking
    this.stopReadingProgressTracking()
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
  background-color: var(--button-primary);
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
  color: var(--text-primary);
}

.loading-spinner {
  border: 4px solid var(--spinner-border);
  border-top: 4px solid var(--spinner-top);
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
  color: var(--error-color);
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
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  transition: box-shadow 0.2s;
  background-color: var(--card-bg);
  color: var(--text-primary);
  display: flex;
  flex-direction: column;
  position: relative;
}

.lesson-card-content {
  cursor: pointer;
  flex: 1;
}

.lesson-card:hover {
  box-shadow: 0 2px 8px var(--shadow);
}

.lesson-card-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
  justify-content: flex-end;
}

.btn-edit, .btn-delete {
  padding: 6px 12px;
  font-size: 0.9em;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-edit {
  background-color: #007bff;
  color: white;
}

.btn-delete {
  background-color: #dc3545;
  color: white;
}

.btn-edit:hover, .btn-delete:hover {
  opacity: 0.9;
}

.lesson-card h3 {
  margin: 0 0 10px 0;
  color: var(--text-primary);
}

.lesson-meta {
  font-size: 0.9em;
  color: var(--text-secondary);
  margin: 10px 0;
}

.lesson-meta span {
  margin-right: 15px;
}

.lesson-preview {
  color: var(--text-tertiary);
  font-size: 0.9em;
  margin-top: 10px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
}

/* Lesson Reader */
.lesson-reader {
  margin-top: 20px;
}

.lesson-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}

.lesson-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.lesson-title-section {
  margin-bottom: 20px;
}

.lesson-title-section h2 {
  margin: 0 0 10px 0;
  color: var(--text-primary);
}

.lesson-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-top: 10px;
}

.listening-stats, .reading-stats, .progress-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 0.9em;
}

.reading-icon, .progress-icon {
  font-size: 1.1em;
}

.status-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75em;
  font-weight: 600;
  text-transform: uppercase;
}

.status-not_started {
  background-color: #e0e0e0;
  color: #666;
}

.status-in_progress {
  background-color: #fff3cd;
  color: #856404;
}

.status-completed {
  background-color: #d4edda;
  color: #155724;
}

.progress-bar-container {
  position: relative;
  width: 100%;
  height: 20px;
  background-color: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
  margin: 8px 0;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #8bc34a);
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.75em;
  font-weight: 600;
  color: #333;
  z-index: 1;
}

.lesson-reading-time {
  margin-top: 5px;
  color: var(--text-secondary);
  font-size: 0.85em;
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
  background: var(--audio-controls-bg);
  border-radius: 8px;
  border: 1px solid var(--border-color);
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
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

.audio-progress {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--audio-progress-bg);
  outline: none;
  cursor: pointer;
  transition: background 0.3s;
}

.audio-progress:hover {
  background: var(--audio-progress-hover);
}

.audio-progress::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--button-primary);
  cursor: pointer;
}

.audio-progress::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--button-primary);
  cursor: pointer;
  border: none;
}

.no-audio-message {
  margin-top: 15px;
  padding: 15px;
  background: var(--warning-bg);
  border-radius: 4px;
  color: var(--warning-text);
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
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 30px;
  margin-top: 20px;
  line-height: 2;
  font-size: 1.1em;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.lesson-text {
  max-width: 100%;
  word-wrap: break-word;
  color: var(--text-primary);
}

.token {
  cursor: pointer;
  padding: 2px 0;
  border-radius: 3px;
  transition: all 0.2s ease;
  display: inline;
  white-space: normal;
  position: relative;
  color: var(--text-primary);
}

.token:hover {
  background-color: var(--token-hover-bg);
  padding: 2px 4px;
  border-radius: 3px;
  box-shadow: 0 2px 4px var(--shadow);
}

.token-clicked {
  background-color: var(--token-clicked-bg);
  padding: 2px 4px;
  border-radius: 3px;
  animation: tokenClick 0.3s ease;
}

.token-added {
  background-color: var(--token-added-bg);
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 500;
  border-bottom: 2px solid var(--token-added-border);
}

.token-added:hover {
  background-color: var(--token-added-bg);
  opacity: 0.8;
}

.token-in-phrase {
  background-color: rgba(100, 181, 246, 0.2);
  padding: 2px 4px;
  border-radius: 3px;
  border-bottom: 2px solid rgba(100, 181, 246, 0.5);
}

.token-in-phrase:hover {
  background-color: rgba(100, 181, 246, 0.3);
}

.token-known {
  background-color: rgba(76, 175, 80, 0.15);
  padding: 2px 4px;
  border-radius: 3px;
  border-bottom: 2px solid rgba(76, 175, 80, 0.5);
}

.token-known:hover {
  background-color: rgba(76, 175, 80, 0.25);
}

.token-unknown {
  background-color: rgba(244, 67, 54, 0.15);
  padding: 2px 4px;
  border-radius: 3px;
  border-bottom: 2px solid rgba(244, 67, 54, 0.5);
}

.token-unknown:hover {
  background-color: rgba(244, 67, 54, 0.25);
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
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 4px 20px var(--shadow);
  min-width: 300px;
  max-width: 500px;
  animation: popoverFadeIn 0.2s ease;
  z-index: 1000;
  color: var(--text-primary);
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
  border-bottom: 1px solid var(--border-color);
}

.popover-header strong {
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: var(--text-primary);
}

.popover-body p {
  margin: 10px 0;
  color: var(--text-primary);
}

.popover-body strong {
  color: var(--text-primary);
}

.sentence-context, .sentence-translation {
  font-style: italic;
  color: var(--text-secondary);
  font-size: 0.9em;
}

/* Dictionary Section Styles */
.dictionary-section {
  margin-bottom: 15px;
}

.meaning-item {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border-color);
}

.meaning-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.part-of-speech {
  margin-bottom: 10px;
}

.pos-tag {
  display: inline-block;
  background: var(--button-primary);
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.75em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.definitions-list {
  list-style: none;
  padding: 0;
  margin: 10px 0;
}

.definition-item {
  padding: 6px 0;
  padding-left: 15px;
  position: relative;
  color: var(--text-primary);
  line-height: 1.5;
}

.definition-item::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--button-primary);
  font-weight: bold;
}

.examples-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-color);
}

.examples-label {
  display: block;
  font-size: 0.85em;
  color: var(--text-secondary);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.examples-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.example-item {
  padding: 4px 0;
  padding-left: 15px;
  position: relative;
  color: var(--text-secondary);
  font-size: 0.9em;
  line-height: 1.4;
}

.example-item::before {
  content: "→";
  position: absolute;
  left: 0;
  color: var(--button-primary);
}

.translation-section {
  margin-bottom: 15px;
}

.sentence-context-section,
.sentence-translation-section {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}

.popover-status-actions {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}

.status-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-status {
  flex: 1;
  min-width: 100px;
  padding: 8px 12px;
  font-size: 0.9em;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-status:hover:not(:disabled) {
  background: var(--bg-hover);
  border-color: var(--button-primary);
}

.btn-status:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-status-active {
  background: var(--button-primary);
  color: white;
  border-color: var(--button-primary);
}

.btn-status-active:hover:not(:disabled) {
  background: var(--button-primary-hover);
}

.btn-status-clear {
  flex: 0 0 auto;
  min-width: auto;
  padding: 8px 16px;
  background: transparent;
  color: var(--text-secondary);
  border-color: var(--border-color);
}

.btn-status-clear:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.popover-actions {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--border-color);
}

.popover-loading {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
}

.popover-loading p {
  margin-top: 10px;
  margin-bottom: 0;
}

.loading-spinner-small {
  border: 3px solid var(--spinner-border);
  border-top: 3px solid var(--spinner-top);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

.no-tokens-message {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary);
  font-style: italic;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

.modal-content {
  background: var(--card-bg);
  border-radius: 8px;
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px var(--shadow);
  color: var(--text-primary);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h2 {
  margin: 0;
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-primary);
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 1em;
  font-family: inherit;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.form-control:focus {
  outline: none;
  border-color: var(--button-primary);
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

textarea.form-control {
  resize: vertical;
  min-height: 150px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

@media (max-width: 768px) {
  .modal-content {
    max-width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
  
  .lesson-header {
    flex-direction: column;
  }
  
  .lesson-actions {
    width: 100%;
    justify-content: flex-end;
  }
}

.token-spacing {
  user-select: text;
  -webkit-user-select: text;
}

/* Toast Notification */
.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px var(--shadow);
  z-index: 10000;
  animation: toastSlideIn 0.3s ease;
  max-width: 400px;
  font-size: 0.95em;
}

.toast-success {
  background-color: var(--success-bg);
  color: var(--success-color);
  border: 1px solid var(--success-color);
}

.toast-error {
  background-color: var(--error-bg);
  color: var(--error-color);
  border: 1px solid var(--error-color);
}

@keyframes toastSlideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .toast {
    bottom: 10px;
    right: 10px;
    left: 10px;
    max-width: none;
  }
}
</style>
