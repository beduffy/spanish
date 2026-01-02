# TTS Debugging Guide

## Current Status

✅ **TTS Generation Works**: When called directly from backend, TTS generates successfully
✅ **Google Cloud API Enabled**: API is enabled and working
✅ **Credentials Configured**: Credentials file is accessible
❌ **Frontend API Call Failing**: Getting 403 authentication error when called from frontend during import

## Issue

When importing a lesson with TTS enabled:
1. Lesson is created successfully ✅
2. TTS API call is made but gets 403 Forbidden ❌
3. Lesson is saved without audio_url ❌
4. User sees "No audio available" message ❌

## Root Cause

The TTS API endpoint requires authentication, but the call during import is getting a 403 error. This suggests:
- Token might not be available yet (timing issue)
- Token might be expired
- Authentication middleware might be rejecting the request

## Solutions

### Option 1: Manual TTS Generation (Quick Fix)

Add a "Generate TTS" button on the lesson detail page that users can click after import.

### Option 2: Retry Mechanism

Add retry logic with delay in the frontend TTS call.

### Option 3: Background Job

Move TTS generation to a background task that runs after lesson creation.

### Option 4: Fix Authentication

Ensure token is properly refreshed before TTS API call.

## Testing

To test TTS generation manually:

1. **Via Browser Console**:
```javascript
// Get your lesson ID (e.g., 6)
ApiService.reader.generateTTS(6).then(r => console.log('TTS Result:', r))
```

2. **Via Backend Shell**:
```bash
docker-compose exec backend python manage.py shell
>>> from flashcards.models import Lesson
>>> from flashcards.tts_service import generate_tts_audio
>>> lesson = Lesson.objects.get(lesson_id=6)
>>> audio_url = generate_tts_audio(lesson.text, 'de-DE')
>>> lesson.audio_url = audio_url
>>> lesson.save()
```

3. **Check Logs**:
```bash
docker-compose logs backend -f | grep -i tts
```

## Next Steps

1. Add manual "Generate TTS" button to ReaderView
2. Add better error handling and retry logic
3. Investigate authentication timing issue
4. Consider moving TTS to background job
