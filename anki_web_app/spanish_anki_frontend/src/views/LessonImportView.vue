<template>
  <div class="lesson-import-view">
    <h1>Import Lesson</h1>

    <div v-if="errorMessage" class="error-message">
      <p>{{ errorMessage }}</p>
    </div>

    <div v-if="successMessage" class="success-message">
      <p>{{ successMessage }}</p>
    </div>

    <div class="import-form">
      <form @submit.prevent="handleImport">
        <div class="form-group">
          <label for="title">Lesson Title *</label>
          <input 
            type="text" 
            id="title" 
            v-model="title" 
            :placeholder="`e.g., ${getLanguageName(language)} News Article - March 2025`"
            required 
          />
        </div>

        <div class="form-group">
          <label for="sourceType">Source Type *</label>
          <select id="sourceType" v-model="sourceType" required>
            <option value="text">Text Paste</option>
            <option value="file">File Upload</option>
            <option value="url">URL</option>
            <option value="youtube">YouTube (Coming Soon)</option>
          </select>
        </div>

        <!-- Text Paste -->
        <div v-if="sourceType === 'text'" class="form-group">
          <label for="text">Text Content *</label>
          <textarea 
            id="text" 
            v-model="text" 
            rows="15"
            :placeholder="`Paste your ${getLanguageName(language)} text here...`"
            required
          ></textarea>
          <small>Text will be automatically tokenized when imported.</small>
        </div>

        <!-- File Upload -->
        <div v-if="sourceType === 'file'" class="form-group">
          <label for="file">Text File *</label>
          <input 
            type="file" 
            id="file" 
            @change="handleFileSelect" 
            accept=".txt,.md"
            required 
          />
          <small v-if="selectedFile">Selected: {{ selectedFile.name }}</small>
        </div>

        <!-- URL -->
        <div v-if="sourceType === 'url'" class="form-group">
          <label for="sourceUrl">Source URL *</label>
          <input 
            type="url" 
            id="sourceUrl" 
            v-model="sourceUrl" 
            placeholder="https://example.com/article"
            required 
          />
          <small>Note: URL content extraction coming soon. For now, paste the text content below.</small>
          <textarea 
            v-model="text" 
            rows="10"
            placeholder="Paste the text content from the URL..."
            required
            style="margin-top: 10px;"
          ></textarea>
        </div>

        <!-- YouTube (Placeholder) -->
        <div v-if="sourceType === 'youtube'" class="form-group">
          <label for="youtubeUrl">YouTube URL</label>
          <input 
            type="url" 
            id="youtubeUrl" 
            v-model="sourceUrl" 
            placeholder="https://www.youtube.com/watch?v=..."
          />
          <small class="info-message">YouTube transcript extraction coming soon!</small>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="language">Language *</label>
            <select id="language" v-model="language" required>
              <option value="de">German (de)</option>
              <option value="es">Spanish (es)</option>
              <option value="fr">French (fr)</option>
              <option value="it">Italian (it)</option>
            </select>
          </div>

          <div class="form-group">
            <label>
              <input type="checkbox" v-model="generateTTS" />
              Generate TTS Audio (requires Google Cloud TTS setup)
            </label>
          </div>
        </div>

        <div v-if="textPreview && textPreview.length > 0" class="preview-section">
          <h3>Preview</h3>
          <div class="preview-text">
            {{ (textPreview || '').substring(0, 500) }}{{ textPreview && textPreview.length > 500 ? '...' : '' }}
          </div>
          <p class="preview-stats">
            Approximate tokens: ~{{ textPreview ? Math.ceil((textPreview || '').split(/\s+/).filter(w => w.length > 0).length) : 0 }}
          </p>
        </div>

        <div class="form-actions">
          <button 
            type="submit" 
            :disabled="isImporting || !isFormValid" 
            class="btn btn-primary"
          >
            {{ isImporting ? 'Importing...' : 'Import Lesson' }}
          </button>
          <router-link to="/reader" class="btn btn-secondary">Cancel</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import ApiService from '../services/ApiService'

export default {
  name: 'LessonImportView',
  data() {
    return {
      title: '',
      text: '',
      sourceType: 'text',
      sourceUrl: '',
      language: 'de',
      selectedFile: null,
      generateTTS: true,
      isLoading: false,
      isImporting: false,
      errorMessage: '',
      successMessage: ''
    }
  },
  computed: {
    textPreview() {
      return this.text || ''
    },
    isFormValid() {
      if (!this.title.trim()) return false
      if (this.sourceType === 'text' && !this.text.trim()) return false
      if (this.sourceType === 'file' && !this.selectedFile) return false
      if (this.sourceType === 'url' && (!this.sourceUrl || !this.text.trim())) return false
      if (this.sourceType === 'youtube') return false // Not implemented yet
      return true
    }
  },
  methods: {
    getLanguageName(code) {
      const languages = {
        'es': 'Spanish',
        'de': 'German',
        'fr': 'French',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'zh': 'Chinese',
        'ko': 'Korean'
      }
      return languages[code] || code.toUpperCase()
    },
    async handleFileSelect(event) {
      const file = event.target.files[0]
      if (!file) return

      this.selectedFile = file
      this.errorMessage = ''

      // Read file content
      try {
        const fileContent = await this.readFileAsText(file)
        this.text = fileContent
      } catch (error) {
        console.error('Error reading file:', error)
        this.errorMessage = 'Failed to read file. Please try again.'
      }
    },
    readFileAsText(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => resolve(e.target.result)
        reader.onerror = reject
        reader.readAsText(file)
      })
    },
    async handleImport() {
      if (!this.isFormValid) {
        this.errorMessage = 'Please fill in all required fields.'
        return
      }

      this.isImporting = true
      this.errorMessage = ''
      this.successMessage = ''

      try {
        const lessonData = {
          title: this.title,
          text: this.text,
          language: this.language,
          source_type: this.sourceType,
          source_url: this.sourceUrl || null
        }

        const response = await ApiService.reader.createLesson(lessonData)
        
        if (response.status === 201 && response.data) {
          const lessonId = response.data.lesson_id
          const tokenCount = response.data.token_count || 0
          this.successMessage = `Lesson imported successfully! (${tokenCount} tokens)`

          // Generate TTS if requested (always try, it's default now)
          // Add delay to ensure session/auth is fully established
          if (this.generateTTS && lessonId) {
            // Wait a bit for session to be established
            await new Promise(resolve => setTimeout(resolve, 500))
            
            try {
              console.log('Generating TTS for lesson:', lessonId)
              
              // Retry mechanism for TTS generation (in case of auth timing issues)
              let ttsResponse = null
              for (let attempt = 0; attempt < 3; attempt++) {
                try {
                  if (attempt > 0) {
                    console.log(`TTS attempt ${attempt + 1}/3`)
                    await new Promise(resolve => setTimeout(resolve, 1000 * attempt))
                  }
                  ttsResponse = await ApiService.reader.generateTTS(lessonId)
                  break // Success, exit retry loop
                } catch (err) {
                  console.warn(`TTS attempt ${attempt + 1} failed:`, err.response?.status, err.response?.data)
                  if (err.response?.status === 403 && attempt < 2) {
                    // Auth error, wait longer and retry
                    continue
                  } else {
                    throw err // Non-auth error or last attempt
                  }
                }
              }
              
              console.log('TTS Response:', ttsResponse)
              
              if (ttsResponse && ttsResponse.data && ttsResponse.data.audio_url) {
                this.successMessage += ' TTS audio generated.'
                console.log('TTS audio URL:', ttsResponse.data.audio_url)
              } else if (ttsResponse && ttsResponse.data && ttsResponse.data.error) {
                console.error('TTS generation failed:', ttsResponse.data.error)
                this.successMessage += ` (TTS: ${ttsResponse.data.error})`
              } else {
                console.error('TTS generation failed: No audio URL returned', ttsResponse)
                this.successMessage += ' (TTS generation failed - you can generate it manually from the lesson page)'
              }
            } catch (ttsError) {
              console.error('TTS generation exception:', ttsError)
              console.error('TTS error response:', ttsError.response)
              const errorMsg = ttsError.response?.data?.error || ttsError.response?.data?.detail || ttsError.message || 'Check API configuration'
              this.successMessage += ` (TTS failed: ${errorMsg} - you can generate it manually from the lesson page)`
            }
          }

          // Redirect back to reader list after a short delay
          if (this.$router) {
            setTimeout(() => {
              this.$router.push({ name: 'Reader' }).catch((err) => {
                console.error('Navigation error:', err)
                // Fallback: try direct path
                this.$router.push('/reader').catch(() => {
                  console.error('Fallback navigation also failed')
                })
              })
            }, 2000)
          }
        } else {
          throw new Error('Invalid response from server')
        }
      } catch (error) {
        console.error('Error importing lesson:', error)
        this.errorMessage = error.response?.data?.error || error.response?.data?.detail || 'Failed to import lesson. Please try again.'
      } finally {
        this.isImporting = false
      }
    }
  }
}
</script>

<style scoped>
.lesson-import-view {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.import-form {
  margin-top: 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.form-group input[type="text"],
.form-group input[type="url"],
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
}

.form-group textarea {
  resize: vertical;
  min-height: 200px;
}

.form-group small {
  display: block;
  margin-top: 5px;
  color: #666;
  font-size: 0.9em;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-group input[type="checkbox"] {
  width: auto;
  margin-right: 8px;
}

.form-group input[type="file"] {
  width: 100%;
  padding: 8px;
}

.preview-section {
  margin: 30px 0;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
}

.preview-section h3 {
  margin-top: 0;
}

.preview-text {
  background: white;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #ddd;
  max-height: 300px;
  overflow-y: auto;
  line-height: 1.6;
  white-space: pre-wrap;
}

.preview-stats {
  margin-top: 10px;
  color: #666;
  font-size: 0.9em;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-primary:disabled {
  background-color: #6c757d;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.success-message {
  background-color: #d4edda;
  color: #155724;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.info-message {
  color: #856404;
  background-color: #fff3cd;
  padding: 8px;
  border-radius: 4px;
  display: block;
  margin-top: 5px;
}
</style>
