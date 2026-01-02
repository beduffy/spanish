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

## Notes

- The implementation maintains backward compatibility with existing flashcard functionality
- All existing database tables and models remain unchanged
- The reader is a new feature that doesn't interfere with existing features
- German is set as the default language throughout, but the system supports multiple languages
- Error handling and logging added throughout for easier debugging

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
