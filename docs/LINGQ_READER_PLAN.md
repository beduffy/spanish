# LingQ-Style Reader Integration Plan

## Overview

Add a LingQ-style reader feature to the existing Spanish Anki flashcard app. The reader will allow users to import text (and eventually YouTube), translate words/sentences, generate TTS audio, and **easily add words/phrases to the existing Card flashcard system**.

**Key Principle**: The reader is a **separate feature** that integrates with the existing Card system. We do NOT modify the Card model or existing flashcard functionality.

---

## Architecture Summary

### New Components

1. **Backend**: New Django app `reader` (or add to `flashcards` app)
   - `Lesson` model: stores imported text/audio
   - `Token` model: stores tokenized words/phrases with positions
   - Translation caching
   - TTS audio generation/storage
   - API endpoints for reader operations

2. **Frontend**: New Vue views/components
   - `ReaderView.vue`: Main reader interface
   - `LessonImportView.vue`: Import text/YouTube
   - Token highlighting and click-to-translate
   - "Add to Flashcards" button integration

3. **Integration Point**
   - Reader → Card: When user clicks "Add to Flashcards", create a Card via existing `/api/flashcards/cards/` endpoint
   - Card fields populated: `front` = word/phrase, `back` = translation, `source` = lesson URL/title, `tags` = ["reader"], `notes` = sentence context

---

## Phase 1: Data Models & Backend Foundation

### 1.1 Database Models (`anki_web_app/flashcards/models.py`)

```python
class Lesson(models.Model):
    """
    Represents an imported text/audio lesson (like a LingQ lesson).
    """
    lesson_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lessons')
    
    title = models.CharField(max_length=500)
    text = models.TextField(help_text="Full text content")
    language = models.CharField(max_length=10, default='es', help_text="Language code (es, de, etc.)")
    
    # Audio support
    audio_url = models.URLField(blank=True, null=True, help_text="URL to audio file")
    audio_file = models.FileField(upload_to='lessons/audio/', blank=True, null=True)
    
    # Source tracking
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('text', 'Text Paste'),
            ('youtube', 'YouTube'),
            ('url', 'URL'),
            ('file', 'File Upload'),
        ],
        default='text'
    )
    source_url = models.URLField(blank=True, null=True, help_text="Original source URL")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Translation cache (sentence-level)
    sentence_translations = models.JSONField(
        default=dict,
        blank=True,
        help_text="Cached translations: {sentence_text: translation}"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"


class Token(models.Model):
    """
    Represents a word/phrase token within a lesson.
    Used for highlighting and click-to-translate.
    """
    token_id = models.AutoField(primary_key=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='tokens')
    
    # Token text and position
    text = models.CharField(max_length=200, help_text="Surface form of the token")
    normalized = models.CharField(max_length=200, db_index=True, help_text="Normalized form (lowercase, punctuation stripped)")
    
    # Position in lesson text
    start_offset = models.IntegerField(help_text="Character offset where token starts")
    end_offset = models.IntegerField(help_text="Character offset where token ends")
    
    # Translation cache (word-level)
    translation = models.TextField(blank=True, null=True, help_text="Cached translation/gloss")
    dictionary_entry = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dictionary data: {meanings: [...], part_of_speech: '...'}"
    )
    
    # User interaction tracking
    clicked_count = models.IntegerField(default=0, help_text="How many times user clicked this token")
    added_to_flashcards = models.BooleanField(default=False, help_text="Whether user added this to flashcards")
    card_id = models.IntegerField(blank=True, null=True, help_text="ID of Card created from this token")
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['start_offset']
        indexes = [
            models.Index(fields=['lesson', 'start_offset']),
            models.Index(fields=['normalized']),
        ]
        verbose_name = "Token"
        verbose_name_plural = "Tokens"


class Phrase(models.Model):
    """
    Represents a multi-word phrase selected by the user.
    """
    phrase_id = models.AutoField(primary_key=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='phrases')
    
    text = models.TextField(help_text="Full phrase text")
    normalized = models.CharField(max_length=500, db_index=True)
    
    # Token references (which tokens make up this phrase)
    token_start = models.ForeignKey(
        Token,
        on_delete=models.CASCADE,
        related_name='phrase_starts',
        help_text="First token in phrase"
    )
    token_end = models.ForeignKey(
        Token,
        on_delete=models.CASCADE,
        related_name='phrase_ends',
        help_text="Last token in phrase"
    )
    
    translation = models.TextField(blank=True, null=True)
    added_to_flashcards = models.BooleanField(default=False)
    card_id = models.IntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['start_offset']
        verbose_name = "Phrase"
        verbose_name_plural = "Phrases"
```

### 1.2 Tokenization Utility (`anki_web_app/flashcards/tokenization.py`)

```python
"""
Tokenization utilities for Spanish (and eventually German).
Uses Intl.Segmenter-like approach for word segmentation.
"""

import re
from typing import List, Dict, Tuple


def normalize_token(text: str) -> str:
    """
    Normalize a token for matching/comparison.
    - Lowercase
    - Strip leading/trailing punctuation
    - Keep umlauts/accents as-is
    """
    # Strip leading/trailing punctuation but keep internal punctuation
    normalized = text.lower().strip()
    # Remove common punctuation from edges
    normalized = re.sub(r'^[.,;:!?()\[\]„""\'…]+', '', normalized)
    normalized = re.sub(r'[.,;:!?()\[\]„""\'…]+$', '', normalized)
    return normalized


def tokenize_spanish(text: str) -> List[Dict[str, any]]:
    """
    Tokenize Spanish text into words and punctuation.
    Returns list of dicts: {text, normalized, start_offset, end_offset, type}
    """
    tokens = []
    # Simple regex-based tokenization (can be improved with spaCy later)
    # Matches words (including accented chars) and punctuation separately
    pattern = r'\w+|[^\w\s]'
    
    offset = 0
    for match in re.finditer(pattern, text):
        token_text = match.group(0)
        start = match.start()
        end = match.end()
        
        # Skip pure whitespace matches
        if token_text.strip():
            tokens.append({
                'text': token_text,
                'normalized': normalize_token(token_text),
                'start_offset': start,
                'end_offset': end,
                'type': 'word' if re.match(r'\w+', token_text) else 'punctuation'
            })
    
    return tokens
```

### 1.3 Translation Service (`anki_web_app/flashcards/translation_service.py`)

```python
"""
Translation service using DeepL API (free tier: 500k chars/month).
Caches translations to avoid redundant API calls.
"""

import os
import requests
from django.core.cache import cache
from typing import Optional


DEEPL_API_KEY = os.getenv('DEEPL_API_KEY', '')
DEEPL_API_URL = 'https://api-free.deepl.com/v2/translate' if not DEEPL_API_KEY.startswith('paid') else 'https://api.deepl.com/v2/translate'


def translate_text(text: str, source_lang: str = 'es', target_lang: str = 'en') -> Optional[str]:
    """
    Translate text using DeepL API.
    Caches results in Django cache.
    """
    if not DEEPL_API_KEY:
        return None
    
    # Check cache first
    cache_key = f"translation:{source_lang}:{target_lang}:{text}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        response = requests.post(
            DEEPL_API_URL,
            data={
                'auth_key': DEEPL_API_KEY,
                'text': text,
                'source_lang': source_lang.upper(),
                'target_lang': target_lang.upper(),
            },
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get('translations'):
            translation = result['translations'][0]['text']
            # Cache for 30 days
            cache.set(cache_key, translation, 60 * 60 * 24 * 30)
            return translation
    except Exception as e:
        print(f"Translation error: {e}")
        return None
    
    return None


def get_word_translation(word: str, source_lang: str = 'es', target_lang: str = 'en') -> Optional[Dict]:
    """
    Get dictionary-style translation for a single word.
    For MVP, just translate the word. Later can integrate with dictionary API.
    """
    translation = translate_text(word, source_lang, target_lang)
    if translation:
        return {
            'word': word,
            'translation': translation,
            'meanings': [translation],  # Simplified for MVP
        }
    return None
```

### 1.4 TTS Service (`anki_web_app/flashcards/tts_service.py`)

```python
"""
Text-to-Speech service using Google Cloud TTS (free tier: 1M chars/month).
Generates audio files and stores them.
"""

import os
from google.cloud import texttospeech
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


GOOGLE_TTS_CREDENTIALS_PATH = os.getenv('GOOGLE_TTS_CREDENTIALS_PATH', '')


def generate_tts_audio(text: str, language_code: str = 'es-ES', output_filename: str = None) -> Optional[str]:
    """
    Generate TTS audio using Google Cloud TTS.
    Returns the file path/URL.
    """
    if not GOOGLE_TTS_CREDENTIALS_PATH or not os.path.exists(GOOGLE_TTS_CREDENTIALS_PATH):
        return None
    
    try:
        client = texttospeech.TextToSpeechClient.from_service_account_file(
            GOOGLE_TTS_CREDENTIALS_PATH
        )
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save to Django storage
        if not output_filename:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            output_filename = f'tts/{text_hash}.mp3'
        
        file_path = default_storage.save(output_filename, ContentFile(response.audio_content))
        return default_storage.url(file_path)
        
    except Exception as e:
        print(f"TTS error: {e}")
        return None
```

---

## Phase 2: Backend API Endpoints

### 2.1 Serializers (`anki_web_app/flashcards/serializers.py` - add to existing file)

```python
class LessonSerializer(serializers.ModelSerializer):
    token_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'lesson_id', 'title', 'text', 'language', 'audio_url',
            'source_type', 'source_url', 'created_at', 'token_count'
        ]
        read_only_fields = ['lesson_id', 'created_at']
    
    def get_token_count(self, obj):
        return obj.tokens.count()


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = [
            'token_id', 'text', 'normalized', 'start_offset', 'end_offset',
            'translation', 'clicked_count', 'added_to_flashcards', 'card_id'
        ]
        read_only_fields = ['token_id', 'clicked_count', 'added_to_flashcards', 'card_id']


class LessonDetailSerializer(LessonSerializer):
    tokens = TokenSerializer(many=True, read_only=True)
    
    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + ['tokens']


class LessonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['title', 'text', 'language', 'audio_url', 'source_type', 'source_url']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        lesson = Lesson.objects.create(**validated_data)
        
        # Tokenize the text
        from .tokenization import tokenize_spanish
        tokens_data = tokenize_spanish(lesson.text)
        
        for token_data in tokens_data:
            Token.objects.create(
                lesson=lesson,
                **token_data
            )
        
        return lesson


class TranslateRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    source_lang = serializers.CharField(default='es')
    target_lang = serializers.CharField(default='en')


class AddToFlashcardsSerializer(serializers.Serializer):
    token_id = serializers.IntegerField(required=False)
    phrase_id = serializers.IntegerField(required=False)
    front = serializers.CharField()  # Word/phrase in source language
    back = serializers.CharField()  # Translation
    sentence_context = serializers.CharField(required=False, allow_blank=True)
    lesson_id = serializers.IntegerField()
    
    def validate(self, attrs):
        if not attrs.get('token_id') and not attrs.get('phrase_id'):
            raise serializers.ValidationError("Either token_id or phrase_id required")
        return attrs
```

### 2.2 Views (`anki_web_app/flashcards/views.py` - add to existing file)

```python
# Add these imports at the top
from .models import Lesson, Token, Phrase
from .serializers import (
    LessonSerializer, LessonDetailSerializer, LessonCreateSerializer,
    TokenSerializer, TranslateRequestSerializer, AddToFlashcardsSerializer
)
from .translation_service import translate_text, get_word_translation
from .tts_service import generate_tts_audio


class LessonListCreateAPIView(UserScopedMixin, ListCreateAPIView):
    """
    List or create lessons.
    POST: Create a new lesson (tokenizes automatically).
    """
    queryset = Lesson.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LessonCreateSerializer
        return LessonSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LessonDetailAPIView(UserScopedMixin, RetrieveAPIView):
    """
    Get lesson details with tokens.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonDetailSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]


class TranslateAPIView(APIView):
    """
    Translate text (word or sentence).
    POST: {text, source_lang, target_lang}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = TranslateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        text = serializer.validated_data['text']
        source_lang = serializer.validated_data.get('source_lang', 'es')
        target_lang = serializer.validated_data.get('target_lang', 'en')
        
        translation = translate_text(text, source_lang, target_lang)
        
        if translation:
            return Response({
                'text': text,
                'translation': translation,
                'source_lang': source_lang,
                'target_lang': target_lang,
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Translation failed. Check API key configuration.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TokenClickAPIView(APIView):
    """
    Record a token click and return translation.
    GET: /api/flashcards/reader/tokens/<token_id>/click/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, token_id, *args, **kwargs):
        try:
            token = Token.objects.get(token_id=token_id, lesson__user=request.user)
        except Token.DoesNotExist:
            return Response({'error': 'Token not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Increment click count
        token.clicked_count += 1
        token.save(update_fields=['clicked_count'])
        
        # Get translation if not cached
        if not token.translation:
            word_translation = get_word_translation(token.text, token.lesson.language, 'en')
            if word_translation:
                token.translation = word_translation.get('translation', '')
                token.save(update_fields=['translation'])
        
        # Get sentence translation (for context)
        lesson = token.lesson
        sentence_text = self._get_sentence_context(lesson.text, token.start_offset)
        sentence_translation = None
        if sentence_text in lesson.sentence_translations:
            sentence_translation = lesson.sentence_translations[sentence_text]
        else:
            sentence_translation = translate_text(sentence_text, lesson.language, 'en')
            if sentence_translation:
                lesson.sentence_translations[sentence_text] = sentence_translation
                lesson.save(update_fields=['sentence_translations'])
        
        return Response({
            'token': TokenSerializer(token).data,
            'sentence': sentence_text,
            'sentence_translation': sentence_translation,
        }, status=status.HTTP_200_OK)
    
    def _get_sentence_context(self, text: str, offset: int) -> str:
        """Extract sentence containing the token."""
        # Find sentence boundaries
        sentence_end = text.find('.', offset)
        sentence_start = text.rfind('.', 0, offset) + 1
        if sentence_start == 0:
            sentence_start = 0
        if sentence_end == -1:
            sentence_end = len(text)
        else:
            sentence_end += 1
        
        return text[sentence_start:sentence_end].strip()


class AddToFlashcardsAPIView(APIView):
    """
    Add a token/phrase to flashcards.
    Creates a Card via existing Card API.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = AddToFlashcardsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        token_id = data.get('token_id')
        phrase_id = data.get('phrase_id')
        front = data['front']
        back = data['back']
        sentence_context = data.get('sentence_context', '')
        lesson_id = data['lesson_id']
        
        # Get lesson
        try:
            lesson = Lesson.objects.get(lesson_id=lesson_id, user=request.user)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create Card using existing CardCreateSerializer logic
        card_data = {
            'front': front,
            'back': back,
            'language': lesson.language,
            'tags': ['reader'],
            'notes': f"From lesson: {lesson.title}\n\nContext: {sentence_context}" if sentence_context else f"From lesson: {lesson.title}",
            'source': lesson.source_url or f"Lesson {lesson.lesson_id}",
            'create_reverse': True,
        }
        
        # Use existing Card creation endpoint logic
        card_serializer = CardCreateSerializer(data=card_data, context={'request': request})
        if not card_serializer.is_valid():
            return Response(card_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        card = card_serializer.save(user=request.user)
        
        # Update token/phrase
        if token_id:
            try:
                token = Token.objects.get(token_id=token_id, lesson=lesson)
                token.added_to_flashcards = True
                token.card_id = card.card_id
                token.save(update_fields=['added_to_flashcards', 'card_id'])
            except Token.DoesNotExist:
                pass
        
        if phrase_id:
            try:
                phrase = Phrase.objects.get(phrase_id=phrase_id, lesson=lesson)
                phrase.added_to_flashcards = True
                phrase.card_id = card.card_id
                phrase.save(update_fields=['added_to_flashcards', 'card_id'])
            except Phrase.DoesNotExist:
                pass
        
        return Response({
            'card_id': card.card_id,
            'message': 'Card created successfully',
        }, status=status.HTTP_201_CREATED)


class GenerateTTSAPIView(APIView):
    """
    Generate TTS audio for a lesson or text snippet.
    POST: {lesson_id, text (optional)}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        lesson_id = request.data.get('lesson_id')
        text = request.data.get('text')
        language_code = request.data.get('language_code', 'es-ES')
        
        if lesson_id:
            try:
                lesson = Lesson.objects.get(lesson_id=lesson_id, user=request.user)
                text = lesson.text
                language_code = f"{lesson.language}-ES"  # Simplified
            except Lesson.DoesNotExist:
                return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not text:
            return Response({'error': 'text or lesson_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        audio_url = generate_tts_audio(text, language_code)
        
        if audio_url:
            # Update lesson audio_url if lesson_id provided
            if lesson_id:
                lesson.audio_url = audio_url
                lesson.save(update_fields=['audio_url'])
            
            return Response({
                'audio_url': audio_url,
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'TTS generation failed. Check API configuration.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### 2.3 URL Routes (`anki_web_app/flashcards/urls.py` - add to existing file)

```python
# Add to imports
from .views import (
    # ... existing imports ...
    LessonListCreateAPIView,
    LessonDetailAPIView,
    TranslateAPIView,
    TokenClickAPIView,
    AddToFlashcardsAPIView,
    GenerateTTSAPIView,
)

# Add to urlpatterns
urlpatterns = [
    # ... existing patterns ...
    
    # Reader endpoints
    path('reader/lessons/', LessonListCreateAPIView.as_view(), name='lesson_list_create_api'),
    path('reader/lessons/<int:pk>/', LessonDetailAPIView.as_view(), name='lesson_detail_api'),
    path('reader/translate/', TranslateAPIView.as_view(), name='translate_api'),
    path('reader/tokens/<int:token_id>/click/', TokenClickAPIView.as_view(), name='token_click_api'),
    path('reader/add-to-flashcards/', AddToFlashcardsAPIView.as_view(), name='add_to_flashcards_api'),
    path('reader/generate-tts/', GenerateTTSAPIView.as_view(), name='generate_tts_api'),
]
```

---

## Phase 3: Frontend Implementation

### 3.1 New Vue Views

#### `ReaderView.vue` - Main Reader Interface

**Location**: `anki_web_app/spanish_anki_frontend/src/views/ReaderView.vue`

**Features**:
- Display lesson text with clickable tokens
- Highlight tokens based on status (unknown/known/added to flashcards)
- Click token → show popover with translation + sentence context
- "Add to Flashcards" button in popover
- Audio player for lesson audio
- Listening time tracking

**Key Components**:
- Token highlighting (CSS classes based on token status)
- Popover component for translations
- Audio player component
- Integration with `ApiService.addToFlashcards()`

#### `LessonImportView.vue` - Import Lessons

**Location**: `anki_web_app/spanish_anki_frontend/src/views/LessonImportView.vue`

**Features**:
- Paste text input
- Upload file option
- YouTube URL input (Phase 2)
- Language selection
- Preview before import
- Generate TTS option

### 3.2 API Service Updates (`ApiService.js`)

```javascript
// Add to ApiService.js

reader: {
  // Lessons
  getLessons() {
    return apiClient.get('/reader/lessons/');
  },
  
  createLesson(lessonData) {
    return apiClient.post('/reader/lessons/', lessonData);
  },
  
  getLesson(lessonId) {
    return apiClient.get(`/reader/lessons/${lessonId}/`);
  },
  
  // Translation
  translateText(text, sourceLang = 'es', targetLang = 'en') {
    return apiClient.post('/reader/translate/', {
      text,
      source_lang: sourceLang,
      target_lang: targetLang,
    });
  },
  
  // Token interaction
  clickToken(tokenId) {
    return apiClient.get(`/reader/tokens/${tokenId}/click/`);
  },
  
  // Add to flashcards
  addToFlashcards(data) {
    return apiClient.post('/reader/add-to-flashcards/', data);
  },
  
  // TTS
  generateTTS(lessonId, text = null, languageCode = 'es-ES') {
    return apiClient.post('/reader/generate-tts/', {
      lesson_id: lessonId,
      text,
      language_code: languageCode,
    });
  },
}
```

### 3.3 Router Updates (`router/index.js`)

```javascript
// Add routes
{
  path: '/reader',
  name: 'Reader',
  component: () => import('../views/ReaderView.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/reader/import',
  name: 'LessonImport',
  component: () => import('../views/LessonImportView.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/reader/lessons/:id',
  name: 'LessonDetail',
  component: () => import('../views/ReaderView.vue'),
  props: true,
  meta: { requiresAuth: true }
},
```

---

## Phase 4: Environment Variables & Configuration

### 4.1 Required Environment Variables

Add to `env.prod.example` and backend settings:

```bash
# DeepL Translation API
DEEPL_API_KEY=your_deepl_api_key_here

# Google Cloud TTS (optional, can use ElevenLabs later)
GOOGLE_TTS_CREDENTIALS_PATH=/path/to/google-credentials.json

# Or ElevenLabs (alternative)
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

### 4.2 Django Settings Updates

```python
# Add to settings.py

# Translation/TTS services
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY', '')
GOOGLE_TTS_CREDENTIALS_PATH = os.getenv('GOOGLE_TTS_CREDENTIALS_PATH', '')

# File storage for TTS audio (if using local storage)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

---

## Phase 5: Migration & Database

### 5.1 Create Migrations

```bash
cd anki_web_app
python manage.py makemigrations flashcards
python manage.py migrate
```

### 5.2 Migration File Structure

The migration will create:
- `Lesson` table
- `Token` table (with indexes)
- `Phrase` table

---

## Phase 6: Testing Strategy

### 6.1 Backend Tests

- Test tokenization (Spanish text → tokens)
- Test translation API integration (mock DeepL)
- Test Card creation from reader
- Test TTS generation (mock Google TTS)

### 6.2 Frontend Tests

- Unit tests for token highlighting
- E2E tests for:
  - Import lesson → tokenize → click token → add to flashcards
  - Verify card appears in card list

---

## Phase 7: Future Enhancements (Post-MVP)

### 7.1 YouTube Integration

- Extract transcript from YouTube URL
- Sync audio with text (timestamps)
- Use `youtube-transcript-api` or similar

### 7.2 Advanced Features

- Phrase selection (drag to select multiple words)
- Dictionary integration (more detailed word meanings)
- Audio-text alignment (timestamps per word)
- Multiple language support (German, etc.)
- Community hints (if multi-user)

---

## Implementation Order (Recommended)

1. **Week 1: Backend Foundation**
   - Day 1-2: Models + migrations
   - Day 3: Tokenization utility
   - Day 4: Translation service (DeepL)
   - Day 5: Basic API endpoints (create lesson, get lesson)

2. **Week 2: Reader Core**
   - Day 1-2: Frontend ReaderView (token display, click handling)
   - Day 3: Translation popover
   - Day 4: "Add to Flashcards" integration
   - Day 5: Lesson import UI

3. **Week 3: Audio & Polish**
   - Day 1-2: TTS integration (Google Cloud or ElevenLabs)
   - Day 3: Audio player + listening time tracking
   - Day 4: UI polish (highlighting, animations)
   - Day 5: Testing + bug fixes

4. **Week 4: YouTube & Advanced**
   - Day 1-3: YouTube transcript extraction
   - Day 4-5: Testing + documentation

---

## Integration Points Summary

### Reader → Flashcards Flow

1. User imports text → `Lesson` created → tokens generated
2. User clicks word → translation fetched → popover shown
3. User clicks "Add to Flashcards" → `Card` created via existing API
4. Card fields:
   - `front`: word/phrase (Spanish)
   - `back`: translation (English)
   - `source`: lesson URL/title
   - `tags`: ["reader"]
   - `notes`: sentence context
   - `language`: "es"
5. Token marked as `added_to_flashcards=True`, `card_id` stored

### No Changes to Existing Card System

- Card model unchanged
- Card API endpoints unchanged
- Card review flow unchanged
- Reader is additive feature only

---

## Cost Estimates (from chat_about_lingq.md)

- **DeepL Free Tier**: 500k characters/month (likely sufficient for 2 users)
- **Google Cloud TTS Free Tier**: 1M characters/month (~16-20 hours of audio)
- **ElevenLabs** (if preferred): $11/mo for ~200 minutes, $99/mo for ~1000 minutes

---

## Notes

- Keep reader feature isolated from existing flashcard code
- Use existing Card API for integration (don't duplicate card creation logic)
- Cache translations aggressively (30 days)
- Generate TTS once per lesson, cache audio files
- Tokenization can be improved later (spaCy, etc.) but simple regex works for MVP
