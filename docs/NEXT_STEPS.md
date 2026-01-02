# Next Steps: LingQ Reader Implementation

## ✅ Completed (Week 1-3)

### Week 1: Backend Foundation ✅
- ✅ Lesson, Token, Phrase models
- ✅ Tokenization utility
- ✅ Translation service (DeepL)
- ✅ Basic API endpoints

### Week 2: Reader Core ✅
- ✅ Frontend ReaderView (token display, click handling)
- ✅ Translation popover
- ✅ "Add to Flashcards" integration
- ✅ Lesson import UI

### Week 3: Audio & Polish ✅
- ✅ TTS integration (Google Cloud TTS + ElevenLabs fallback)
- ✅ Audio player with listening time tracking
- ✅ UI polish (highlighting, animations)
- ✅ Comprehensive test coverage (46 tests total)

---

## ⏳ Next: Week 4 - YouTube & Advanced Features

### Priority 1: YouTube Transcript Extraction (Days 1-3)

**What's Needed:**
1. **Backend**: YouTube transcript extraction service
   - Use `youtube-transcript-api` Python library
   - Extract transcript from YouTube URL
   - Parse timestamps and text
   - Create Lesson with transcript as text
   - Optionally download audio (if needed)

2. **Frontend**: YouTube URL handling
   - Update `LessonImportView.vue` to handle YouTube URLs
   - Show loading state while extracting transcript
   - Display transcript preview before import
   - Handle errors (private videos, no transcript, etc.)

**Implementation Steps:**
```python
# New file: anki_web_app/flashcards/youtube_service.py
from youtube_transcript_api import YouTubeTranscriptApi

def extract_youtube_transcript(video_url):
    """
    Extract transcript from YouTube URL.
    Returns: {text: str, language: str, timestamps: List[Dict]}
    """
    # Parse video ID from URL
    # Call YouTube Transcript API
    # Format transcript text
    # Return structured data
```

**Dependencies to Add:**
- `youtube-transcript-api` (Python package)
- Update `requirements.txt`

**Files to Modify:**
- `anki_web_app/flashcards/youtube_service.py` (new)
- `anki_web_app/flashcards/views.py` (add YouTube import endpoint)
- `anki_web_app/spanish_anki_frontend/src/views/LessonImportView.vue` (enable YouTube import)
- `anki_web_app/flashcards/urls.py` (add YouTube endpoint)

---

### Priority 2: Advanced Features (Future)

#### 2.1 Phrase Selection (Multi-word)
**What's Needed:**
- Frontend: Drag-to-select multiple tokens
- Backend: Create Phrase model entries
- UI: Highlight selected phrase, show translation
- Integration: Add phrase to flashcards

**Status:** Phrase model exists, but UI not implemented

#### 2.2 Dictionary Integration
**What's Needed:**
- Enhanced word meanings (beyond simple translation)
- Part of speech, example sentences
- Could integrate with:
  - DeepL dictionary API (if available)
  - Wiktionary API
  - Custom dictionary database

**Status:** Basic translation exists, dictionary data not implemented

#### 2.3 Audio-Text Alignment
**What's Needed:**
- Word-level timestamps in audio
- Highlight words as audio plays
- Sync playback with text highlighting

**Status:** Not implemented (requires advanced TTS or manual alignment)

#### 2.4 Progress Tracking Per Lesson
**What's Needed:**
- Track which tokens user has "learned"
- Progress percentage per lesson
- Vocabulary mastery tracking

**Status:** Basic listening time tracking exists, but no vocabulary progress

#### 2.5 Vocabulary Lists Generation
**What's Needed:**
- Export vocabulary from lessons
- Generate word lists with translations
- CSV/Anki format export

**Status:** Not implemented

---

## Implementation Priority

### High Priority (Week 4)
1. **YouTube Transcript Extraction** - Most requested feature
   - Enables importing YouTube videos directly
   - Makes reader much more useful
   - Estimated: 2-3 days

### Medium Priority (Future)
2. **Phrase Selection** - Improves UX significantly
   - Multi-word phrases are common
   - Better flashcard creation
   - Estimated: 2-3 days

3. **Progress Tracking** - Useful for learning
   - See which words you've mastered
   - Track learning progress
   - Estimated: 2-3 days

### Low Priority (Nice to Have)
4. **Dictionary Integration** - Enhanced word info
5. **Audio-Text Alignment** - Advanced feature
6. **Vocabulary Lists Export** - Convenience feature

---

## Quick Start: YouTube Integration

### Step 1: Install Dependency
```bash
# Add to requirements.txt
youtube-transcript-api==0.6.1
```

### Step 2: Create YouTube Service
```python
# anki_web_app/flashcards/youtube_service.py
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import re

def extract_video_id(url):
    """Extract YouTube video ID from URL."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_transcript(video_url):
    """
    Get transcript from YouTube video.
    Returns: {text: str, language: str, timestamps: List}
    """
    video_id = extract_video_id(video_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")
    
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English or German transcript first
        transcript = None
        for t in transcript_list:
            if t.language_code in ['en', 'de', 'es']:
                transcript = t.fetch()
                break
        
        # Fallback to first available
        if not transcript:
            transcript = transcript_list[0].fetch()
        
        # Combine text
        text = ' '.join([entry['text'] for entry in transcript])
        language = transcript[0].get('language', 'en')
        
        return {
            'text': text,
            'language': language,
            'timestamps': transcript
        }
    except Exception as e:
        raise ValueError(f"Failed to get transcript: {str(e)}")
```

### Step 3: Add API Endpoint
```python
# In views.py
class YouTubeImportAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        url = request.data.get('url')
        if not url:
            return Response({'error': 'URL required'}, status=400)
        
        try:
            transcript_data = get_youtube_transcript(url)
            # Create lesson with transcript
            lesson = Lesson.objects.create(
                user=request.user,
                title=f"YouTube Video",
                text=transcript_data['text'],
                language=transcript_data['language'],
                source_type='youtube',
                source_url=url
            )
            # Tokenize...
            return Response(LessonSerializer(lesson).data, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
```

### Step 4: Update Frontend
```javascript
// In LessonImportView.vue
async importYouTubeLesson() {
  try {
    const response = await ApiService.reader.importYouTube(this.youtubeUrl);
    // Handle success...
  } catch (error) {
    // Handle error...
  }
}
```

---

## Testing Checklist

### YouTube Integration
- [ ] Extract transcript from public video
- [ ] Handle private/unavailable videos
- [ ] Handle videos without transcripts
- [ ] Support multiple language transcripts
- [ ] Create lesson with YouTube source
- [ ] Tokenize YouTube transcript correctly

### Advanced Features (Future)
- [ ] Select multiple tokens for phrase
- [ ] Create phrase from selection
- [ ] Add phrase to flashcards
- [ ] Track vocabulary progress
- [ ] Export vocabulary lists

---

## Notes

- **YouTube API**: No API key needed for transcript extraction (uses public API)
- **Rate Limits**: YouTube transcript API has rate limits (check library docs)
- **Language Detection**: Auto-detect language from transcript
- **Error Handling**: Handle cases where transcript unavailable
- **Privacy**: Some videos don't have transcripts (private, disabled, etc.)
