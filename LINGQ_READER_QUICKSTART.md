# LingQ Reader Quick Start Guide

## What We're Building

A LingQ-style reader that lets you:
1. **Import text** (paste, upload file, or YouTube URL)
2. **Click words** to get instant translations
3. **Add words/phrases** directly to your existing flashcard deck
4. **Listen to TTS audio** of the text

## Key Integration Point

**Reader → Flashcards**: When you click "Add to Flashcards" in the reader, it creates a `Card` using your existing `/api/flashcards/cards/` endpoint. No changes to your Card system!

## Implementation Phases

### Phase 1: Backend Models & API (Week 1)
- [ ] Create `Lesson`, `Token`, `Phrase` models
- [ ] Add tokenization utility (Spanish text → tokens)
- [ ] Add translation service (DeepL API)
- [ ] Create API endpoints:
  - `POST /api/flashcards/reader/lessons/` - Import lesson
  - `GET /api/flashcards/reader/lessons/<id>/` - Get lesson with tokens
  - `GET /api/flashcards/reader/tokens/<id>/click/` - Click token, get translation
  - `POST /api/flashcards/reader/add-to-flashcards/` - Create Card from token

### Phase 2: Frontend Reader (Week 2)
- [ ] Create `ReaderView.vue` - Main reader interface
- [ ] Create `LessonImportView.vue` - Import text/YouTube
- [ ] Token highlighting (unknown/known/added)
- [ ] Click-to-translate popover
- [ ] "Add to Flashcards" button integration

### Phase 3: Audio & Polish (Week 3)
- [ ] TTS service (Google Cloud or ElevenLabs)
- [ ] Audio player component
- [ ] Listening time tracking
- [ ] UI polish

### Phase 4: YouTube (Week 4)
- [ ] YouTube transcript extraction
- [ ] Audio-text sync

## Environment Setup

Add to `.env`:
```bash
DEEPL_API_KEY=your_key_here
GOOGLE_TTS_CREDENTIALS_PATH=/path/to/credentials.json  # Optional
```

## Database Migration

```bash
cd anki_web_app
python manage.py makemigrations flashcards
python manage.py migrate
```

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/flashcards/reader/lessons/` | GET, POST | List/create lessons |
| `/api/flashcards/reader/lessons/<id>/` | GET | Get lesson with tokens |
| `/api/flashcards/reader/translate/` | POST | Translate text |
| `/api/flashcards/reader/tokens/<id>/click/` | GET | Click token, get translation |
| `/api/flashcards/reader/add-to-flashcards/` | POST | Create Card from token/phrase |
| `/api/flashcards/reader/generate-tts/` | POST | Generate TTS audio |

## Frontend Routes

- `/reader` - Main reader (list lessons)
- `/reader/import` - Import new lesson
- `/reader/lessons/:id` - View specific lesson

## How It Works

1. **Import**: User pastes text → `Lesson` created → text tokenized → `Token` objects created
2. **Read**: User views lesson → tokens highlighted by status → click token → popover shows translation
3. **Add**: User clicks "Add to Flashcards" → `Card` created via existing API → token marked as added

## Card Creation Details

When adding a token to flashcards:
- `front`: Word/phrase in Spanish
- `back`: Translation in English
- `source`: Lesson title/URL
- `tags`: ["reader"]
- `notes`: Sentence context
- `language`: "es"
- `create_reverse`: True (creates reverse card automatically)

## Cost Estimates

- **DeepL**: Free tier = 500k chars/month (sufficient for 2 users)
- **Google TTS**: Free tier = 1M chars/month (~16-20 hours audio)
- **ElevenLabs**: $11/mo = 200 minutes, $99/mo = 1000 minutes

## Files to Create/Modify

### Backend
- `anki_web_app/flashcards/models.py` - Add Lesson, Token, Phrase models
- `anki_web_app/flashcards/tokenization.py` - NEW: Tokenization utility
- `anki_web_app/flashcards/translation_service.py` - NEW: DeepL integration
- `anki_web_app/flashcards/tts_service.py` - NEW: TTS generation
- `anki_web_app/flashcards/serializers.py` - Add reader serializers
- `anki_web_app/flashcards/views.py` - Add reader API views
- `anki_web_app/flashcards/urls.py` - Add reader routes

### Frontend
- `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue` - NEW
- `anki_web_app/spanish_anki_frontend/src/views/LessonImportView.vue` - NEW
- `anki_web_app/spanish_anki_frontend/src/services/ApiService.js` - Add reader methods
- `anki_web_app/spanish_anki_frontend/src/router/index.js` - Add reader routes

## Testing Checklist

- [ ] Import lesson → verify tokens created
- [ ] Click token → verify translation appears
- [ ] Add to flashcards → verify Card created
- [ ] Verify card appears in card list
- [ ] Verify card has correct tags/notes
- [ ] Test TTS generation
- [ ] Test audio playback

## Next Steps

1. Start with Phase 1: Backend models
2. Test tokenization with sample Spanish text
3. Set up DeepL API key
4. Build basic API endpoints
5. Move to frontend

See `LINGQ_READER_PLAN.md` for detailed implementation guide.
