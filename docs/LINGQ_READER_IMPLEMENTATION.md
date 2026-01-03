# LingQ-Style Reader Implementation Summary

## Overview

This document summarizes the implementation of a LingQ-style reader feature for the Spanish Anki web application. The reader allows users to import text lessons, tokenize them into clickable words/phrases, translate individual tokens, and add them to flashcards.

**Date**: January 2, 2026  
**Status**: Implemented with German as default language

## Key Requirements

1. **Preserve Existing Functionality**: All existing app and database functionality must remain intact
2. **Docker Environment**: All changes must work within the existing Docker Compose setup
3. **Default Language**: German (user primarily cares about German, not Spanish)
4. **Error Handling**: Fix all console errors, both existing and new ones

## Architecture

### Backend (Django)

#### New Models (`anki_web_app/flashcards/models.py`)

1. **Lesson Model**
   - Stores text content, language, optional audio URL
   - Fields: `lesson_id`, `title`, `text`, `language` (default: 'de'), `audio_url`, `source_type`, `source_url`, `user`, `sentence_translations`, `created_at`, `updated_at`

2. **Token Model**
   - Represents individual words/punctuation within a lesson
   - Fields: `token_id`, `lesson`, `text`, `normalized`, `start_offset`, `end_offset`, `translation`, `dictionary_entry`, `clicked_count`, `added_to_flashcards`, `card_id`, `created_at`

3. **Phrase Model**
   - Represents multi-word phrases
   - Fields: `phrase_id`, `lesson`, `text`, `normalized`, `translation`, `start_token`, `end_token`, `added_to_flashcards`, `card_id`, `created_at`

#### New Utilities

1. **Tokenization (`anki_web_app/flashcards/tokenization.py`)**
   - Function: `tokenize_text(text, language='de')`
   - Breaks text into tokens with offsets and normalized forms
   - Language-agnostic (currently uses general regex, can be extended for language-specific rules)

2. **Translation Service (`anki_web_app/flashcards/translation_service.py`)**
   - Functions: `translate_text(text, source_lang='de', target_lang='en')`, `get_word_translation(word, source_lang='de', target_lang='en')`
   - Integrates with DeepL API
   - Includes caching for translations

3. **TTS Service (`anki_web_app/flashcards/tts_service.py`)**
   - Function: `generate_tts_audio(text, language_code='de-DE', output_path=None)`
   - Integrates with Google Cloud TTS
   - Generates audio files for lessons

#### New Serializers (`anki_web_app/flashcards/serializers.py`)

1. **LessonSerializer**: Basic lesson representation with `token_count`
2. **LessonDetailSerializer**: Includes full token list
3. **LessonCreateSerializer**: Handles lesson creation and automatic tokenization
4. **TokenSerializer**: Token representation
5. **TranslateRequestSerializer**: For translation API requests
6. **AddToFlashcardsSerializer**: For adding tokens to flashcards

#### New API Views (`anki_web_app/flashcards/views.py`)

1. **LessonListCreateAPIView**: List and create lessons
2. **LessonDetailAPIView**: Get lesson details with tokens
3. **TranslateAPIView**: Translate text/tokens
4. **TokenClickAPIView**: Track token clicks
5. **AddToFlashcardsAPIView**: Add tokens to flashcards
6. **GenerateTTSAPIView**: Generate TTS audio for lessons

#### URL Routes (`anki_web_app/flashcards/urls.py`)

All reader endpoints are under `/api/flashcards/reader/`:
- `GET/POST /lessons/` - List/create lessons
- `GET /lessons/<id>/` - Get lesson details
- `POST /translate/` - Translate text
- `POST /tokens/<id>/click/` - Track token click
- `POST /tokens/<id>/add-to-flashcards/` - Add token to flashcards
- `POST /lessons/<id>/generate-tts/` - Generate TTS audio

### Frontend (Vue.js 3)

#### New Components

1. **ReaderView.vue** (`anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue`)
   - Main reader interface
   - Displays lesson list and lesson detail views
   - Handles clickable tokens with translation popovers
   - Integrates audio playback
   - Features:
     - Token highlighting on click
     - Translation display
     - "Add to Flashcards" functionality
     - Empty state messages

2. **LessonImportView.vue** (`anki_web_app/spanish_anki_frontend/src/views/LessonImportView.vue`)
   - Lesson import interface
   - Supports:
     - Text paste
     - File upload
     - URL input
   - Language selection (default: German)
   - Optional TTS generation
   - Dynamic placeholders based on selected language

#### Updated Components

1. **App.vue**: Added navigation link to reader section
2. **LoginView.vue**: Fixed ESLint errors and improved login redirect timing

#### API Service (`anki_web_app/spanish_anki_frontend/src/services/ApiService.js`)

Added `reader` namespace with methods:
- `getLessons(page=1)`
- `createLesson(lessonData)`
- `getLesson(lessonId)`
- `translateText(text, sourceLang='de', targetLang='en')`
- `clickToken(tokenId)`
- `addToFlashcards(tokenId)`
- `generateTTS(lessonId, languageCode='de-DE')`

Improved authentication:
- Enhanced `getAccessToken()` to refresh session if token expired
- Added retry logic in Axios interceptor for missing tokens
- Better error handling

#### Router (`anki_web_app/spanish_anki_frontend/src/router/index.js`)

New routes:
- `/reader` - Lesson list view
- `/reader/import` - Lesson import view
- `/reader/lessons/:id` - Lesson detail view

## Configuration Changes

### Django Settings (`anki_web_app/spanish_anki_project/settings.py`)

- Added `MEDIA_ROOT` and `MEDIA_URL` for serving audio files
- Updated Supabase environment variable loading to explicitly use `os.environ` as fallback

### Docker Compose (`docker-compose.yml`)

- Added `SUPABASE_URL` and `SUPABASE_JWT_SECRET` to backend service environment variables

### URL Configuration (`anki_web_app/spanish_anki_project/urls.py`)

- Added media file serving for development: `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)`

## Issues Encountered and Fixes

### Issue 1: Module Build Error in ReaderView.vue
**Error**: `TypeError: Cannot read properties of null (reading 'content')`  
**Cause**: Duplicate `methods:` declaration  
**Fix**: Merged duplicate methods into single `methods` object

### Issue 2: ESLint Errors
**Error**: Unused variables (`newId`, `result`)  
**Fix**: Removed unused parameters from watchers and variables

### Issue 3: 403 Forbidden Errors After Login
**Error**: All API requests returning 403 after successful login  
**Causes**:
- Supabase JWT token not being consistently sent
- Environment variables not passed to Docker container
- Token refresh timing issues

**Fixes**:
- Updated `SupabaseService.getAccessToken()` to refresh session if token expired
- Added retry mechanism in Axios request interceptor
- Added delay after login before redirect
- Added `SUPABASE_URL` and `SUPABASE_JWT_SECRET` to Docker Compose environment
- Updated `settings.py` to explicitly read from `os.environ` as fallback
- Recreated backend container to apply environment variables

### Issue 4: Database Tables Missing
**Error**: `django.db.utils.OperationalError: no such table: flashcards_lesson`  
**Fix**: Ran migrations:
```bash
docker-compose exec backend python manage.py makemigrations flashcards
docker-compose exec backend python manage.py migrate
```

### Issue 5: 500 Error on Lesson Creation
**Error**: Lesson created but no tokens generated  
**Cause**: Tokenization function returns `type` field, but Token model doesn't have it  
**Fix**: Filter out `type` field before creating Token objects:
```python
token_data_clean = {k: v for k, v in token_data.items() if k != 'type'}
```

### Issue 6: Redirect Not Working After Lesson Creation
**Error**: Lesson created but didn't redirect to reader view  
**Fix**: 
- Improved redirect logic with fallback
- Added `token_count` to serializer response
- Ensured `lesson_id` is converted to string for router

## Language Defaults Changed

All Spanish defaults changed to German:

1. **Lesson Model**: `language` default changed from 'es' to 'de'
2. **Translation Service**: `source_lang` default changed from 'es' to 'de'
3. **TTS Service**: `language_code` default changed from 'es-ES' to 'de-DE'
4. **API Views**: Defaults updated to German
5. **Frontend**: Default language selection set to 'de'
6. **Placeholders**: Dynamic based on selected language (e.g., "German News Article" instead of "Spanish News Article")

## Database Migrations

New migrations created:
- `0007_lesson_token_phrase_and_more.py` - Creates Lesson, Token, and Phrase tables

## Testing

### Manual Testing Steps

1. **Login**: Verify authentication works
2. **Import Lesson**: 
   - Navigate to `/reader/import`
   - Paste German text
   - Select language (default: German)
   - Create lesson
   - Verify tokens are created
   - Verify redirect to lesson detail view
3. **View Lesson**:
   - Click on tokens
   - Verify translation popover appears
   - Test "Add to Flashcards" functionality
   - Test audio playback (if TTS generated)
4. **List Lessons**:
   - Navigate to `/reader`
   - Verify lesson list displays
   - Verify pagination works

## Environment Variables Required

### Backend (.env or Docker Compose)

- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_JWT_SECRET` - Supabase JWT secret for token verification
- `DEEPL_API_KEY` - DeepL API key for translations (optional)
- `GOOGLE_CLOUD_TTS_CREDENTIALS` - Google Cloud credentials JSON for TTS (optional)

### Frontend

- Supabase configuration handled via `SupabaseService.js`

## Future Enhancements

1. **Language-Specific Tokenization**: Extend `tokenize_text()` with language-specific rules
2. **Phrase Detection**: Implement automatic phrase detection
3. **Dictionary Integration**: Add dictionary lookup for tokens
4. **Progress Tracking**: Track reading progress per lesson
5. **Vocabulary Lists**: Generate vocabulary lists from lessons
6. **Export**: Export lessons and vocabulary to Anki format

## Files Modified

### Backend
- `anki_web_app/flashcards/models.py` - Added Lesson, Token, Phrase models
- `anki_web_app/flashcards/tokenization.py` - Created tokenization utility
- `anki_web_app/flashcards/translation_service.py` - Created translation service
- `anki_web_app/flashcards/tts_service.py` - Created TTS service
- `anki_web_app/flashcards/serializers.py` - Added reader serializers
- `anki_web_app/flashcards/views.py` - Added reader API views
- `anki_web_app/flashcards/urls.py` - Added reader URL routes
- `anki_web_app/spanish_anki_project/settings.py` - Added media configuration
- `anki_web_app/spanish_anki_project/urls.py` - Added media serving

### Frontend
- `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue` - Created reader view
- `anki_web_app/spanish_anki_frontend/src/views/LessonImportView.vue` - Created import view
- `anki_web_app/spanish_anki_frontend/src/views/App.vue` - Added navigation link
- `anki_web_app/spanish_anki_frontend/src/views/LoginView.vue` - Fixed errors
- `anki_web_app/spanish_anki_frontend/src/services/ApiService.js` - Added reader API methods
- `anki_web_app/spanish_anki_frontend/src/router/index.js` - Added reader routes

### Configuration
- `docker-compose.yml` - Added environment variables

## Recent Updates (January 2, 2026)

### DeepL Translation Integration
- **DeepL API Key Configured**: Added `DEEPL_API_KEY` environment variable to `docker-compose.yml`
- **Translation Service Working**: Verified translation functionality for both sentences and single words
- **Context Storage**: Enhanced flashcard creation to include sentence context and translation in notes field
- **Card Serializer Updated**: Added `language` and `source` fields to `CardCreateSerializer` to ensure they're saved

### UI Improvements
- **Notes Column Added**: Added "Notes" column to All Cards page (`CardListView.vue`) to display context/notes
- **Enhanced Notes Formatting**: Notes now include:
  - Lesson title
  - Original sentence context (in source language)
  - Sentence translation (in target language)

## Caching Strategy

The reader feature uses a two-level caching strategy to minimize API calls and improve performance:

### 1. Django Cache (Translation Service)
- **Location**: `anki_web_app/flashcards/translation_service.py`
- **Cache Backend**: Django's default cache (in-memory or database cache)
- **Cache Key Format**: `translation:{source_lang}:{target_lang}:{text}`
- **TTL**: 30 days (2,592,000 seconds)
- **Purpose**: Caches DeepL API translation responses to avoid redundant API calls
- **Implementation**:
  ```python
  cache_key = f"translation:{source_lang}:{target_lang}:{text}"
  cached = cache.get(cache_key)
  if cached:
      return cached
  # ... API call ...
  cache.set(cache_key, translation, 60 * 60 * 24 * 30)
  ```

### 2. Database Caching (Lesson Model)
- **Location**: `anki_web_app/flashcards/models.py` - `Lesson` model
- **Field**: `sentence_translations` (JSONField)
- **Format**: `{sentence_text: translation}`
- **Purpose**: Persists sentence translations in the database for long-term storage
- **Usage**: When a token is clicked, the sentence translation is:
  1. Checked in `lesson.sentence_translations` dict
  2. If not found, fetched via DeepL API
  3. Stored in both Django cache and database
  4. Used when creating flashcards to include context

### 3. Token-Level Caching
- **Location**: `Token` model - `translation` field
- **Purpose**: Stores word-level translations directly on tokens
- **Usage**: When a token is clicked, if `token.translation` is empty, it's fetched and saved

### Cache Benefits
- **Reduced API Costs**: DeepL free tier is 500k chars/month - caching helps stay within limits
- **Faster Response Times**: Cached translations return instantly
- **Better User Experience**: No waiting for API calls on repeated clicks
- **Persistence**: Database caching ensures translations survive cache clears

## Notes

- The implementation maintains backward compatibility with existing flashcard functionality
- All existing database tables and models remain unchanged
- The reader is a new feature that doesn't interfere with existing features
- German is set as the default language throughout, but the system supports multiple languages
- Error handling and logging added throughout for easier debugging
- Context from reader lessons is now visible in the All Cards page

## What's Next (From LINGQ_READER_PLAN.md)

Based on the implementation plan, the next phases are:

### Phase 3: Audio & Polish (Week 3)
1. **TTS Integration** (Days 1-2)
   - Complete Google Cloud TTS integration (currently basic implementation exists)
   - Or integrate ElevenLabs as alternative
   - Generate audio files for lessons
   - Store audio URLs in Lesson model

2. **Audio Player** (Day 3)
   - Implement audio playback in ReaderView
   - Add listening time tracking
   - Sync audio with text (optional)

3. **UI Polish** (Day 4)
   - Improve token highlighting animations
   - Enhance popover styling
   - Add loading states
   - Improve mobile responsiveness

4. **Testing & Bug Fixes** (Day 5)
   - Write E2E tests for reader flow
   - Fix any remaining issues
   - Performance optimization

### Phase 4: Advanced Features (Next Steps)

**Note**: YouTube integration deferred - users can manually extract transcripts using tools like y2doc and paste text directly.

**Recommended Next Features** (in order of priority):

1. **Dictionary Integration** (High Priority)
   - Integrate with dictionary API (e.g., Wiktionary, DeepL dictionary)
   - Show multiple meanings, part of speech, example sentences
   - Enhance popover with richer word information
   - Store dictionary entries in `Token.dictionary_entry` JSONField

2. **Progress Tracking** (Medium Priority)
   - Track reading progress per lesson (words read, time spent)
   - Mark lessons as "in progress", "completed"
   - Show progress indicators in lesson list
   - Track vocabulary growth over time

3. **Vocabulary Lists** (Medium Priority)
   - Generate vocabulary lists from lessons
   - Export to CSV/Anki format
   - Filter by "unknown words", "added to flashcards", etc.
   - Statistics: total words, known words, learning words

4. **Audio-Text Alignment** (Lower Priority)
   - Word-level timestamps for audio sync
   - Highlight words as audio plays
   - Click word to jump to audio position
   - Requires more advanced TTS or manual alignment

5. **YouTube Integration** (Deferred)
   - Extract transcripts from YouTube URLs
   - Sync audio with text timestamps
   - Use `youtube-transcript-api` or similar library
   - **Status**: Deferred - users can use y2doc or similar tools manually

### Current Status
- ✅ Backend models and API endpoints
- ✅ Frontend reader interface
- ✅ Translation integration (DeepL)
- ✅ Token click and flashcard creation
- ✅ Context storage in flashcards
- ✅ TTS audio generation (Google Cloud TTS + ElevenLabs fallback)
- ✅ Audio player with listening time tracking
- ✅ UI polish and animations
- ✅ Comprehensive test coverage (46 tests total: 33 original + 13 new integration tests)
- ✅ Phrase selection (multi-word drag selection) - Completed January 2026
- ✅ Token spacing fix - Visual spacing matches copied text
- ✅ Toast notifications for flashcard additions
- ⏳ YouTube transcript extraction (deferred - user can use y2doc manually)
- ⏳ Dictionary integration (more detailed word meanings)
- ⏳ Progress tracking per lesson
- ⏳ Vocabulary lists generation

## Commands Reference

### Database Migrations
```bash
docker-compose exec backend python manage.py makemigrations flashcards
docker-compose exec backend python manage.py migrate
```

### View Backend Logs
```bash
docker-compose logs backend --tail=50 -f
```

### Restart Backend
```bash
docker-compose restart backend
```

### Check Database Tables
```bash
docker-compose exec backend python manage.py shell -c "from flashcards.models import Lesson, Token, Phrase; print('Lesson table exists:', Lesson._meta.db_table)"
```

---

## Week 3 Implementation: TTS Integration & Audio Player (January 2, 2026)

### Completed Features

#### 1. Enhanced TTS Integration
- **Google Cloud TTS**: Primary TTS service with proper language code mapping
- **ElevenLabs Fallback**: Automatic fallback to ElevenLabs if Google TTS is unavailable
- **Language Code Mapping**: Proper mapping from language codes (de, es, fr, etc.) to TTS format (de-DE, es-ES, etc.)
- **Error Handling**: Improved error messages and fallback logic

**Files Modified:**
- `anki_web_app/flashcards/tts_service.py` - Added ElevenLabs support and improved error handling
- `anki_web_app/flashcards/views.py` - Fixed language code mapping in `GenerateTTSAPIView`
- `anki_web_app/requirements.txt` - Added `google-cloud-texttospeech==2.16.3`

#### 2. Listening Time Tracking
- **Database Fields**: Added `total_listening_time_seconds` and `last_listened_at` to Lesson model
- **API Endpoint**: New `/api/flashcards/reader/lessons/<id>/listening-time/` endpoint
- **Frontend Tracking**: Automatic tracking of play/pause events with 5-second update intervals
- **Migration**: Created `0008_add_listening_time_tracking.py`

**Files Modified:**
- `anki_web_app/flashcards/models.py` - Added listening time fields
- `anki_web_app/flashcards/views.py` - Added `UpdateListeningTimeAPIView`
- `anki_web_app/flashcards/serializers.py` - Added listening time fields and formatted display
- `anki_web_app/flashcards/urls.py` - Added listening time endpoint
- `anki_web_app/spanish_anki_frontend/src/services/ApiService.js` - Added `updateListeningTime` method

#### 3. Enhanced Audio Player UI
- **Controls**: Play/pause button with visual state indication
- **Progress Bar**: Seekable slider for audio navigation
- **Time Display**: Current time / total duration (MM:SS format)
- **Listening Stats**: Displays total listening time in lesson header
- **Auto-update**: Listening time updates automatically during playback

**Files Modified:**
- `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue` - Complete audio player overhaul

#### 4. UI Polish & Animations
- **Token Animations**: Click animations and hover effects
- **Popover Styling**: Fade-in animations and improved shadows
- **Loading States**: Spinners for lesson loading and translation loading
- **Mobile Responsiveness**: Responsive layout for audio controls, lesson grid, and popover
- **Visual Feedback**: Enhanced token highlighting with animations

**Files Modified:**
- `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue` - Added animations and responsive styles

#### 5. Google Cloud TTS Setup
- **Credentials Configuration**: Mounted credentials file in Docker
- **Environment Variables**: Configured `GOOGLE_TTS_CREDENTIALS_PATH`
- **Default Selection**: TTS generation checkbox defaults to checked
- **Redirect Behavior**: After lesson import, redirects to reader list (not lesson detail)

**Files Modified:**
- `docker-compose.yml` - Added credentials mount and environment variables
- `anki_web_app/spanish_anki_frontend/src/views/LessonImportView.vue` - Default TTS enabled, redirect to reader list

**Documentation Created:**
- `docs/GOOGLE_TTS_SETUP.md` - Detailed setup guide
- `docs/GOOGLE_TTS_QUICKSTART.md` - Quick reference

### Deployment Checklist

#### Pre-Deployment

1. **Google Cloud TTS Credentials**:
   - Ensure credentials file is available on the server: `~/.google-cloud/google-tts-credentials.json`
   - File should have read permissions: `chmod 644 ~/.google-cloud/google-tts-credentials.json`
   - Verify credentials have "Cloud Text-to-Speech API User" role

2. **Environment Variables** (in production `.env` or deployment config):
   ```bash
   GOOGLE_TTS_CREDENTIALS_PATH=/app/google-tts-credentials.json
   ELEVENLABS_API_KEY=your_key_here  # Optional fallback
   ```

3. **Docker Compose Production** (`docker-compose.prod.yml`):
   ```yaml
   services:
     backend:
       volumes:
         - ~/.google-cloud/google-tts-credentials.json:/app/google-tts-credentials.json:ro
       environment:
         - GOOGLE_TTS_CREDENTIALS_PATH=/app/google-tts-credentials.json
   ```

4. **Database Migrations**:
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

5. **Media Storage**:
   - Ensure `MEDIA_ROOT` is writable: `chmod 755 /path/to/media`
   - TTS audio files will be stored in `media/tts/` directory
   - Configure web server (Nginx) to serve media files:
     ```nginx
     location /media/ {
         alias /path/to/media/;
     }
     ```

#### Deployment Steps

1. **Pull Latest Code**:
   ```bash
   git pull origin main
   ```

2. **Rebuild Backend Container** (to install google-cloud-texttospeech):
   ```bash
   docker-compose -f docker-compose.prod.yml build backend
   docker-compose -f docker-compose.prod.yml up -d backend
   ```

3. **Run Migrations**:
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
   ```

4. **Verify TTS Setup**:
   ```bash
   # Check credentials file is accessible
   docker-compose -f docker-compose.prod.yml exec backend ls -la /app/google-tts-credentials.json
   
   # Test TTS initialization
   docker-compose -f docker-compose.prod.yml exec backend python -c "from google.cloud import texttospeech; import os; client = texttospeech.TextToSpeechClient.from_service_account_file(os.getenv('GOOGLE_TTS_CREDENTIALS_PATH')); print('✓ TTS initialized')"
   ```

5. **Check Logs**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs backend | grep -i tts
   ```

#### Production Considerations

1. **Media File Serving**:
   - TTS audio files are stored in Django's `MEDIA_ROOT`
   - Ensure Nginx/Apache is configured to serve `/media/` URLs
   - Consider using cloud storage (S3, GCS) for production scalability

2. **TTS Costs**:
   - Google Cloud TTS free tier: 4M chars/month (Standard), 1M chars/month (WaveNet)
   - Monitor usage in Google Cloud Console
   - Set up billing alerts if approaching limits

3. **ElevenLabs Alternative**:
   - If Google TTS quota exceeded, system automatically falls back to ElevenLabs
   - Configure `ELEVENLABS_API_KEY` environment variable
   - ElevenLabs pricing: $11/mo for ~200 minutes

4. **Audio File Cleanup**:
   - Audio files are cached by text hash (MD5)
   - Same text generates same audio file (reused)
   - Consider periodic cleanup of unused audio files

5. **Error Handling**:
   - TTS failures are logged but don't block lesson creation
   - Users see warning message if TTS generation fails
   - Check backend logs for detailed error messages

### Testing Checklist

- [ ] Import lesson with TTS enabled
- [ ] Verify audio file is generated and stored
- [ ] Test audio playback in reader view
- [ ] Verify listening time tracking updates
- [ ] Test progress bar and seek functionality
- [ ] Verify mobile responsiveness
- [ ] Test TTS generation failure fallback
- [ ] Verify redirect to reader list after import

### Known Issues & Future Improvements

1. **Audio URL Format**: Currently uses Django's `MEDIA_URL` - ensure it's absolute URL in production
2. **Large Text Handling**: Very long lessons may hit TTS character limits - consider chunking
3. **Audio Quality**: Currently uses Standard voices - could upgrade to WaveNet for better quality
4. **Caching**: Audio files are cached by text hash - consider adding cache headers for browser caching
5. **Error Recovery**: If TTS fails during import, user can manually trigger TTS generation later

### Critical Deployment Step: Enable Google Cloud TTS API

**Before deploying, you MUST enable the Text-to-Speech API in Google Cloud Console:**

1. Go to: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com
2. Select your project (the one matching your credentials file - check the project ID in your JSON credentials)
3. Click **Enable**
4. Wait 2-5 minutes for the API to be fully activated

**If you see error "SERVICE_DISABLED" or "API has not been used":**
- The API is not enabled - this is the most common issue
- Enable it using the link above or the URL provided in the error message
- Wait a few minutes after enabling before retrying

**Verify API is enabled:**
- Check in Google Cloud Console under APIs & Services > Enabled APIs
- Test TTS generation - should work after API is enabled

### Files Changed Summary

**Backend:**
- `anki_web_app/flashcards/models.py` - Added listening time fields
- `anki_web_app/flashcards/views.py` - TTS improvements, listening time endpoint
- `anki_web_app/flashcards/serializers.py` - Added listening time serialization
- `anki_web_app/flashcards/tts_service.py` - ElevenLabs fallback, improved error handling
- `anki_web_app/flashcards/urls.py` - Added listening time route
- `anki_web_app/flashcards/migrations/0008_add_listening_time_tracking.py` - New migration
- `anki_web_app/requirements.txt` - Added google-cloud-texttospeech

**Frontend:**
- `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue` - Audio player, listening tracking, UI polish
- `anki_web_app/spanish_anki_frontend/src/views/LessonImportView.vue` - Default TTS enabled, redirect fix
- `anki_web_app/spanish_anki_frontend/src/services/ApiService.js` - Added listening time method

**Configuration:**
- `docker-compose.yml` - Added credentials mount and TTS environment variables

**Documentation:**
- `docs/GOOGLE_TTS_SETUP.md` - Detailed setup guide
- `docs/GOOGLE_TTS_QUICKSTART.md` - Quick reference

### Testing

**Test Coverage Added:**
- Created comprehensive test suite in `anki_web_app/flashcards/tests_reader.py`
- **33 new tests** covering all reader features:
  - Tokenization utility tests (4 tests)
  - Lesson model tests (3 tests)
  - Token model tests (2 tests)
  - Lesson API tests (6 tests)
  - Translation API tests (2 tests)
  - Token click API tests (3 tests)
  - Add to flashcards API tests (2 tests)
  - TTS API tests (3 tests)
  - Listening time API tests (3 tests)
  - Translation service tests (2 tests)
  - TTS service tests (3 tests)

**Test Files:**
- `anki_web_app/flashcards/tests_reader.py` - All reader feature tests

**Running Reader Tests:**
```bash
# Run all reader tests
docker-compose exec backend python manage.py test flashcards.tests_reader

# Run specific test class
docker-compose exec backend python manage.py test flashcards.tests_reader.LessonAPITests

# Run with verbose output
docker-compose exec backend python manage.py test flashcards.tests_reader -v 2
```

**Test Coverage:**
- ✅ Tokenization (normalize, tokenize with punctuation, offsets)
- ✅ Lesson CRUD operations (create, list, detail, user scoping)
- ✅ Token operations (create, click tracking)
- ✅ Translation API (success, failure, caching)
- ✅ TTS generation (success, failure, lesson not found)
- ✅ Listening time tracking (update, accumulate, not found)
- ✅ Add to flashcards integration (card creation, notes)
- ✅ User scoping (users can only access their own lessons/tokens)

**New Integration Tests Added (13 tests):**
- ✅ TTS Integration Tests (6 tests): Language code mapping, authentication, lesson updates
- ✅ Listening Time Integration Tests (4 tests): Time formatting, serialization, updates
- ✅ Lesson Import Flow Tests (3 tests): Full import flow, TTS generation flow, token positions

All tests pass successfully! ✅

### TTS Auto-Generation During Import

The frontend attempts to auto-generate TTS after lesson import:
1. Lesson is created via `/api/flashcards/reader/lessons/` POST endpoint
2. Response includes `lesson_id` and `token_count`
3. Frontend waits 500ms for session/auth to be established
4. Frontend calls `/api/flashcards/reader/generate-tts/` with `lesson_id`
5. Retry mechanism: up to 3 attempts with exponential backoff (1s, 2s delays)
6. If TTS generation fails, user can manually generate from lesson page

**Troubleshooting TTS Auto-Generation:**
- Check browser console for TTS generation errors
- Verify `lesson_id` is present in lesson creation response
- Check backend logs for TTS service errors
- Ensure Google Cloud TTS API is enabled
- Verify credentials file exists at configured path
- Check ElevenLabs API key if using fallback

---

## Commit Summary (January 2, 2026)

### Changes Committed

**Backend:**
- ✅ Fixed `LessonCreateSerializer` to include `lesson_id` in response
- ✅ Added `token_count` to lesson creation response
- ✅ Enhanced TTS error handling with detailed logging
- ✅ Added comprehensive integration tests (13 new tests)

**Frontend:**
- ✅ Fixed audio URL handling to use absolute backend URL in development
- ✅ Enhanced error logging for TTS generation failures
- ✅ Improved console logging for debugging TTS auto-generation

**Tests:**
- ✅ Added `TTSIntegrationTests` (6 tests): Language mapping, authentication, lesson updates
- ✅ Added `ListeningTimeIntegrationTests` (4 tests): Time formatting, serialization, updates
- ✅ Added `LessonImportFlowTests` (3 tests): Full import flow, TTS generation, token positions
- ✅ All 13 new tests passing successfully

**Documentation:**
- ✅ Updated implementation doc with test coverage details
- ✅ Documented TTS auto-generation flow and troubleshooting steps

**Files Modified:**
- `anki_web_app/flashcards/serializers.py` - Added `lesson_id` and `token_count` to response
- `anki_web_app/flashcards/views.py` - Enhanced TTS error handling
- `anki_web_app/flashcards/tests_reader.py` - Added 13 integration tests
- `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue` - Fixed audio URL handling
- `anki_web_app/spanish_anki_frontend/src/views/LessonImportView.vue` - Enhanced error logging
- `docs/LINGQ_READER_IMPLEMENTATION.md` - Updated with test coverage and troubleshooting

**Status:** ✅ All tests passing, TTS working, ready for next phase

---

## Recent Updates (January 2026 - Phrase Selection & Spacing Fixes)

### Phrase Selection Implementation
- **Multi-word Selection**: Users can now drag-select multiple words to create phrases
- **Backend API**: New `/api/flashcards/reader/phrases/create/` endpoint
- **Frontend Integration**: Mouse selection detection and phrase creation
- **Phrase Model**: Stores multi-word selections with token references
- **Translation**: Phrases are automatically translated when created
- **Flashcard Integration**: Phrases can be added to flashcards just like single tokens

**Files Modified:**
- `anki_web_app/flashcards/models.py` - Phrase model already existed
- `anki_web_app/flashcards/serializers.py` - Added `PhraseSerializer` and `CreatePhraseSerializer`
- `anki_web_app/flashcards/views.py` - Added `CreatePhraseAPIView`
- `anki_web_app/flashcards/urls.py` - Added phrase creation route
- `anki_web_app/spanish_anki_frontend/src/services/ApiService.js` - Added `createPhrase()` method
- `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue` - Added phrase selection logic

### Token Spacing Fix
- **Issue**: Visual spacing between tokens appeared larger than actual spacing when copied
- **Root Cause**: `display: inline-block` with padding was adding extra visual space
- **Solution**: 
  - Changed tokens to `display: inline` with no horizontal padding by default
  - Added padding back on hover/click/added states for visual feedback
  - Enhanced `getTokenSpacing()` to remove spaces before punctuation
  - Normalized spacing after punctuation tokens
- **Result**: Visual spacing now exactly matches copied text

**Files Modified:**
- `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue` - Updated token CSS and spacing logic

### Toast Notifications
- **Replaced**: All `alert()` calls with non-intrusive toast notifications
- **Features**: Auto-dismissing, positioned bottom-right, success/error styling
- **UX Improvement**: Better user experience for flashcard additions

**Files Modified:**
- `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue` - Added toast notification system

### Authentication & UI Fixes
- **Conditional Rendering**: Navigation and logout button only show when user is logged in
- **Auth Backend**: Improved error handling for JWKS verification with fallback mechanisms

**Files Modified:**
- `anki_web_app/spanish_anki_frontend/src/views/App.vue` - Added `v-if="user"` directives
- `anki_web_app/flashcards/auth_backend.py` - Enhanced error handling and fallbacks
