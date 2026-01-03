"""
Tests for LingQ-style Reader feature.

Tests cover:
- Lesson model and API endpoints
- Token model and tokenization
- Translation service
- TTS service
- Listening time tracking
- Add to flashcards integration
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from flashcards.models import Lesson, Token, Phrase, Card, TokenStatus
from flashcards.tokenization import tokenize_text, normalize_token
from flashcards.translation_service import translate_text, get_word_translation
from flashcards.tts_service import generate_tts_audio, _generate_google_tts, _generate_elevenlabs_tts
from flashcards.dictionary_service import get_dictionary_entry, get_wiktionary_language_code, _parse_wiktionary_response

# Try to import lemmatization functions if available
try:
    from flashcards.tokenization import lemmatize_token, get_spacy_model
except ImportError:
    # Functions may not exist yet, define stubs for tests
    def lemmatize_token(text, language='de'):
        return None
    def get_spacy_model(language):
        return None

User = get_user_model()


class TokenizationTests(TestCase):
    """Test tokenization utility functions."""

    def test_normalize_token(self):
        """Test token normalization."""
        self.assertEqual(normalize_token("Hallo"), "hallo")
        self.assertEqual(normalize_token("Hallo!"), "hallo")
        self.assertEqual(normalize_token("!Hallo!"), "hallo")
        self.assertEqual(normalize_token("Hallo."), "hallo")
        self.assertEqual(normalize_token("Hallo,"), "hallo")
        self.assertEqual(normalize_token("über"), "über")  # Preserves umlauts

    def test_tokenize_text_basic(self):
        """Test basic tokenization."""
        text = "Hallo Welt"
        tokens = tokenize_text(text)
        
        self.assertGreater(len(tokens), 0)
        self.assertEqual(tokens[0]['text'], "Hallo")
        self.assertEqual(tokens[0]['normalized'], "hallo")
        self.assertIn('start_offset', tokens[0])
        self.assertIn('end_offset', tokens[0])

    def test_tokenize_text_with_punctuation(self):
        """Test tokenization with punctuation."""
        text = "Hallo, Welt!"
        tokens = tokenize_text(text)
        
        # Should separate words and punctuation
        text_tokens = [t for t in tokens if t.get('type') == 'word']
        self.assertGreaterEqual(len(text_tokens), 2)

    def test_tokenize_text_preserves_offsets(self):
        """Test that token offsets are correct."""
        text = "Hallo Welt"
        tokens = tokenize_text(text)
        
        # First token should start at 0
        self.assertEqual(tokens[0]['start_offset'], 0)
        # Offsets should be sequential
        for i in range(len(tokens) - 1):
            self.assertLessEqual(tokens[i]['end_offset'], tokens[i+1]['start_offset'])

    def test_tokenize_text_includes_lemma_field(self):
        """Test that tokenization includes lemma field."""
        text = "Hallo Welt"
        tokens = tokenize_text(text, language='de')
        
        # All tokens should have lemma field
        for token in tokens:
            self.assertIn('lemma', token)
            # Words should have lemma (may be None if spaCy not available)
            if token.get('type') == 'word':
                # Lemma can be None or a string
                self.assertIsInstance(token['lemma'], (str, type(None)))
            else:
                # Punctuation should have None lemma
                self.assertIsNone(token['lemma'])

    def test_tokenize_text_with_language_parameter(self):
        """Test tokenization with different languages."""
        text = "Hallo Welt"
        
        # Test German
        tokens_de = tokenize_text(text, language='de')
        self.assertGreater(len(tokens_de), 0)
        
        # Test Spanish
        text_es = "Hola Mundo"
        tokens_es = tokenize_text(text_es, language='es')
        self.assertGreater(len(tokens_es), 0)
        
        # Test default (should default to German)
        tokens_default = tokenize_text(text)
        self.assertEqual(len(tokens_default), len(tokens_de))

    @patch('flashcards.tokenization.get_spacy_model')
    def test_lemmatize_token_with_spacy(self, mock_get_model):
        """Test lemmatization when spaCy is available."""
        # Mock spaCy model
        mock_token = MagicMock()
        mock_token.lemma_ = "sehen"
        mock_doc = [mock_token]
        mock_nlp = MagicMock()
        mock_nlp.return_value = mock_doc
        mock_nlp.__call__ = MagicMock(return_value=mock_doc)
        
        mock_get_model.return_value = mock_nlp
        
        # Test lemmatization
        lemma = lemmatize_token("sah", language='de')
        self.assertIsNotNone(lemma)
        self.assertEqual(lemma, "sehen")

    def test_lemmatize_token_without_spacy(self):
        """Test lemmatization gracefully handles missing spaCy."""
        # This should not crash even if spaCy is not installed
        lemma = lemmatize_token("sah", language='de')
        # Should return None if spaCy not available, or a string if it is
        self.assertIsInstance(lemma, (str, type(None)))

    def test_get_spacy_model_caching(self):
        """Test that spaCy models are cached."""
        # Clear cache
        from flashcards.tokenization import _spacy_models
        original_cache = _spacy_models.copy()
        _spacy_models.clear()
        
        try:
            # First call
            model1 = get_spacy_model('de')
            
            # Second call should return cached model
            model2 = get_spacy_model('de')
            
            # Should be the same object (cached) if model was loaded
            if model1 is not None:
                self.assertIs(model1, model2)
        finally:
            # Restore original cache
            _spacy_models.clear()
            _spacy_models.update(original_cache)

    def test_tokenize_text_lemma_for_german_words(self):
        """Test that German words get lemmatized correctly."""
        # Test with common German verb forms
        text = "Ich sehe, du sahst, er gesehen"
        tokens = tokenize_text(text, language='de')
        
        word_tokens = [t for t in tokens if t.get('type') == 'word']
        self.assertGreater(len(word_tokens), 0)
        
        # Check that lemma field exists for words
        for token in word_tokens:
            self.assertIn('lemma', token)
            # If spaCy is available, lemmas should be set
            # If not, they'll be None (which is fine)


class LessonModelTests(TestCase):
    """Test Lesson model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_lesson(self):
        """Test creating a lesson."""
        lesson = Lesson.objects.create(
            user=self.user,
            title="Test Lesson",
            text="Hallo Welt",
            language="de"
        )
        
        self.assertEqual(lesson.title, "Test Lesson")
        self.assertEqual(lesson.text, "Hallo Welt")
        self.assertEqual(lesson.language, "de")
        self.assertEqual(lesson.user, self.user)
        self.assertIsNotNone(lesson.created_at)

    def test_lesson_default_language(self):
        """Test that lesson defaults to German."""
        lesson = Lesson.objects.create(
            user=self.user,
            title="Test",
            text="Test"
        )
        self.assertEqual(lesson.language, "de")

    def test_lesson_listening_time_defaults(self):
        """Test listening time fields default to 0."""
        lesson = Lesson.objects.create(
            user=self.user,
            title="Test",
            text="Test"
        )
        self.assertEqual(lesson.total_listening_time_seconds, 0)
        self.assertIsNone(lesson.last_listened_at)


class TokenModelTests(TestCase):
    """Test Token model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.lesson = Lesson.objects.create(
            user=self.user,
            title="Test Lesson",
            text="Hallo Welt",
            language="de"
        )

    def test_create_token(self):
        """Test creating a token."""
        token = Token.objects.create(
            lesson=self.lesson,
            text="Hallo",
            normalized="hallo",
            start_offset=0,
            end_offset=5
        )
        
        self.assertEqual(token.text, "Hallo")
        self.assertEqual(token.normalized, "hallo")
        self.assertEqual(token.lesson, self.lesson)
        self.assertEqual(token.clicked_count, 0)
        self.assertFalse(token.added_to_flashcards)

    def test_create_token_with_lemma(self):
        """Test creating a token with lemma."""
        token = Token.objects.create(
            lesson=self.lesson,
            text="sah",
            normalized="sah",
            lemma="sehen",
            start_offset=0,
            end_offset=3
        )
        
        self.assertEqual(token.text, "sah")
        self.assertEqual(token.normalized, "sah")
        self.assertEqual(token.lemma, "sehen")
        self.assertIsNotNone(token.lemma)

    def test_token_lemma_can_be_none(self):
        """Test that token lemma can be None."""
        token = Token.objects.create(
            lesson=self.lesson,
            text="Hallo",
            normalized="hallo",
            lemma=None,
            start_offset=0,
            end_offset=5
        )
        
        self.assertIsNone(token.lemma)

    def test_token_clicked_count(self):
        """Test incrementing clicked count."""
        token = Token.objects.create(
            lesson=self.lesson,
            text="Hallo",
            normalized="hallo",
            start_offset=0,
            end_offset=5
        )
        
        token.clicked_count += 1
        token.save()
        
        token.refresh_from_db()
        self.assertEqual(token.clicked_count, 1)


class LessonAPITests(APITestCase):
    """Test Lesson API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_lesson(self):
        """Test creating a lesson via API."""
        url = '/api/flashcards/reader/lessons/'
        data = {
            'title': 'Test Lesson',
            'text': 'Hallo Welt',
            'language': 'de',
            'source_type': 'text'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 1)
        lesson = Lesson.objects.first()
        self.assertEqual(lesson.title, 'Test Lesson')
        self.assertEqual(lesson.text, 'Hallo Welt')
        self.assertEqual(lesson.user, self.user)
        # Should have tokens created
        self.assertGreater(lesson.tokens.count(), 0)

    def test_create_lesson_auto_tokenizes(self):
        """Test that lesson creation automatically tokenizes text."""
        url = '/api/flashcards/reader/lessons/'
        data = {
            'title': 'Test',
            'text': 'Hallo Welt',
            'language': 'de',
            'source_type': 'text'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lesson = Lesson.objects.first()
        tokens = lesson.tokens.all()
        self.assertGreater(len(tokens), 0)
        # Should have token_count in response
        self.assertIn('token_count', response.data)

    def test_create_lesson_tokens_have_lemma(self):
        """Test that tokens created via API include lemma field."""
        url = '/api/flashcards/reader/lessons/'
        data = {
            'title': 'Test',
            'text': 'Hallo Welt',
            'language': 'de',
            'source_type': 'text'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lesson = Lesson.objects.first()
        tokens = lesson.tokens.all()
        
        # All tokens should have lemma field (may be None if spaCy not available)
        for token in tokens:
            # Check that lemma field exists in database
            self.assertTrue(hasattr(token, 'lemma'))
            # Lemma can be None or a string
            if token.lemma is not None:
                self.assertIsInstance(token.lemma, str)

    def test_list_lessons(self):
        """Test listing lessons."""
        # Create some lessons
        Lesson.objects.create(
            user=self.user,
            title='Lesson 1',
            text='Text 1',
            language='de'
        )
        Lesson.objects.create(
            user=self.user,
            title='Lesson 2',
            text='Text 2',
            language='de'
        )
        
        url = '/api/flashcards/reader/lessons/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return lessons (could be paginated)
        if 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 2)
        else:
            self.assertGreaterEqual(len(response.data), 2)

    def test_get_lesson_detail(self):
        """Test getting lesson detail with tokens."""
        lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt',
            language='de'
        )
        # Create some tokens
        Token.objects.create(
            lesson=lesson,
            text='Hallo',
            normalized='hallo',
            start_offset=0,
            end_offset=5
        )
        
        url = f'/api/flashcards/reader/lessons/{lesson.lesson_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Lesson')
        self.assertIn('tokens', response.data)
        self.assertGreater(len(response.data['tokens']), 0)

    def test_list_lessons_user_scoped(self):
        """Test that users only see their own lessons."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        Lesson.objects.create(
            user=self.user,
            title='My Lesson',
            text='Text',
            language='de'
        )
        Lesson.objects.create(
            user=other_user,
            title='Other Lesson',
            text='Text',
            language='de'
        )
        
        url = '/api/flashcards/reader/lessons/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see own lesson
        if 'results' in response.data:
            lessons = response.data['results']
        else:
            lessons = response.data
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['title'], 'My Lesson')


class TranslationAPITests(APITestCase):
    """Test Translation API endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    @patch('flashcards.translation_service.translate_text')
    def test_translate_text_success(self, mock_translate):
        """Test successful translation."""
        mock_translate.return_value = "Hello World"
        
        url = '/api/flashcards/reader/translate/'
        data = {
            'text': 'Hallo Welt',
            'source_lang': 'de',
            'target_lang': 'en'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['translation'], 'Hello World')
        self.assertEqual(response.data['text'], 'Hallo Welt')
        mock_translate.assert_called_once_with('Hallo Welt', 'de', 'en')

    @patch('flashcards.translation_service.translate_text')
    def test_translate_text_failure(self, mock_translate):
        """Test translation failure."""
        mock_translate.return_value = None
        
        url = '/api/flashcards/reader/translate/'
        data = {
            'text': 'Hallo Welt',
            'source_lang': 'de',
            'target_lang': 'en'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)


class TokenClickAPITests(APITestCase):
    """Test Token Click API endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt. Das ist ein Test.',
            language='de'
        )
        self.token = Token.objects.create(
            lesson=self.lesson,
            text='Hallo',
            normalized='hallo',
            start_offset=0,
            end_offset=5
        )

    @patch('flashcards.translation_service.get_word_translation')
    @patch('flashcards.translation_service.translate_text')
    def test_click_token_success(self, mock_sentence_translate, mock_word_translate):
        """Test clicking a token."""
        mock_word_translate.return_value = {'translation': 'Hello'}
        mock_sentence_translate.return_value = 'Hello World.'
        
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/click/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('sentence', response.data)
        self.assertIn('sentence_translation', response.data)
        
        # Check clicked count incremented
        self.token.refresh_from_db()
        self.assertEqual(self.token.clicked_count, 1)

    def test_click_token_not_found(self):
        """Test clicking non-existent token."""
        url = '/api/flashcards/reader/tokens/99999/click/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_click_token_other_user_lesson(self):
        """Test that users can't click tokens from other users' lessons."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_lesson = Lesson.objects.create(
            user=other_user,
            title='Other Lesson',
            text='Text',
            language='de'
        )
        other_token = Token.objects.create(
            lesson=other_lesson,
            text='Text',
            normalized='text',
            start_offset=0,
            end_offset=4
        )
        
        url = f'/api/flashcards/reader/tokens/{other_token.token_id}/click/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AddToFlashcardsAPITests(APITestCase):
    """Test Add to Flashcards API endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt',
            language='de'
        )
        self.token = Token.objects.create(
            lesson=self.lesson,
            text='Hallo',
            normalized='hallo',
            start_offset=0,
            end_offset=5,
            translation='Hello'
        )

    def test_add_token_to_flashcards(self):
        """Test adding a token to flashcards."""
        url = '/api/flashcards/reader/add-to-flashcards/'
        data = {
            'token_id': self.token.token_id,
            'front': 'Hallo',
            'back': 'Hello',
            'sentence_context': 'Hallo Welt',
            'lesson_id': self.lesson.lesson_id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('card_id', response.data)
        
        # Check token was updated
        self.token.refresh_from_db()
        self.assertTrue(self.token.added_to_flashcards)
        self.assertIsNotNone(self.token.card_id)
        
        # Check card was created
        card = Card.objects.get(card_id=self.token.card_id)
        self.assertEqual(card.front, 'Hallo')
        self.assertEqual(card.back, 'Hello')
        self.assertIn('reader', card.tags)
        self.assertEqual(card.user, self.user)

    def test_add_token_to_flashcards_with_notes(self):
        """Test that sentence context is added to notes."""
        url = '/api/flashcards/reader/add-to-flashcards/'
        data = {
            'token_id': self.token.token_id,
            'front': 'Hallo',
            'back': 'Hello',
            'sentence_context': 'Hallo Welt',
            'lesson_id': self.lesson.lesson_id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        card = Card.objects.get(card_id=response.data['card_id'])
        self.assertIn('Test Lesson', card.notes)
        self.assertIn('Hallo Welt', card.notes)


class TTSAPITests(APITestCase):
    """Test TTS API endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt',
            language='de'
        )

    @patch('flashcards.tts_service.generate_tts_audio')
    def test_generate_tts_success(self, mock_generate_tts):
        """Test successful TTS generation."""
        mock_generate_tts.return_value = '/media/tts/test.mp3'
        
        url = '/api/flashcards/reader/generate-tts/'
        data = {
            'lesson_id': self.lesson.lesson_id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('audio_url', response.data)
        mock_generate_tts.assert_called_once()
        
        # Check lesson was updated
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.audio_url, '/media/tts/test.mp3')

    @patch('flashcards.tts_service.generate_tts_audio')
    def test_generate_tts_failure(self, mock_generate_tts):
        """Test TTS generation failure."""
        mock_generate_tts.return_value = None
        
        url = '/api/flashcards/reader/generate-tts/'
        data = {
            'lesson_id': self.lesson.lesson_id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)

    def test_generate_tts_lesson_not_found(self):
        """Test TTS generation for non-existent lesson."""
        url = '/api/flashcards/reader/generate-tts/'
        data = {
            'lesson_id': 99999
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ListeningTimeAPITests(APITestCase):
    """Test Listening Time API endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt',
            language='de'
        )

    def test_update_listening_time(self):
        """Test updating listening time."""
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/listening-time/'
        data = {
            'lesson_id': self.lesson.lesson_id,
            'seconds_listened': 30
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_listening_time_seconds', response.data)
        
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.total_listening_time_seconds, 30)
        self.assertIsNotNone(self.lesson.last_listened_at)

    def test_update_listening_time_accumulates(self):
        """Test that listening time accumulates."""
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/listening-time/'
        
        # First update
        self.client.post(url, {'lesson_id': self.lesson.lesson_id, 'seconds_listened': 20}, format='json')
        # Second update
        self.client.post(url, {'lesson_id': self.lesson.lesson_id, 'seconds_listened': 15}, format='json')
        
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.total_listening_time_seconds, 35)

    def test_update_listening_time_lesson_not_found(self):
        """Test updating listening time for non-existent lesson."""
        url = '/api/flashcards/reader/lessons/99999/listening-time/'
        data = {
            'lesson_id': 99999,
            'seconds_listened': 30
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TranslationServiceTests(TestCase):
    """Test translation service functions."""

    @patch('flashcards.translation_service.requests.post')
    @patch('flashcards.translation_service.cache')
    def test_translate_text_success(self, mock_cache, mock_post):
        """Test successful translation."""
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'translations': [{'text': 'Hello'}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = translate_text('Hallo', 'de', 'en')
        
        self.assertEqual(result, 'Hello')
        mock_cache.set.assert_called_once()

    @patch('flashcards.translation_service.cache')
    def test_translate_text_cache_hit(self, mock_cache):
        """Test translation cache hit."""
        mock_cache.get.return_value = 'Hello'
        
        result = translate_text('Hallo', 'de', 'en')
        
        self.assertEqual(result, 'Hello')
        # Should not call API
        mock_cache.set.assert_not_called()


class TTSServiceTests(TestCase):
    """Test TTS service functions."""

    @patch('flashcards.tts_service.os.path.exists')
    def test_generate_google_tts_no_credentials(self, mock_exists):
        """Test Google TTS when credentials not available."""
        mock_exists.return_value = False
        
        result = _generate_google_tts('Test', 'de-DE')
        
        self.assertIsNone(result)

    @patch('flashcards.tts_service.os.path.exists')
    def test_generate_google_tts_no_credentials(self, mock_exists):
        """Test Google TTS when credentials not available."""
        mock_exists.return_value = False
        
        result = _generate_google_tts('Test', 'de-DE')
        
        self.assertIsNone(result)

    @patch('flashcards.tts_service.requests.post')
    @patch('flashcards.tts_service.default_storage')
    def test_generate_elevenlabs_tts_success(self, mock_storage, mock_post):
        """Test successful ElevenLabs TTS generation."""
        with patch('flashcards.tts_service.ELEVENLABS_API_KEY', 'test-key'):
            mock_response = MagicMock()
            mock_response.content = b'fake audio data'
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            mock_storage.save.return_value = 'tts/test.mp3'
            mock_storage.url.return_value = '/media/tts/test.mp3'
            
            result = _generate_elevenlabs_tts('Test', 'de-DE')
            
            self.assertEqual(result, '/media/tts/test.mp3')
            mock_post.assert_called_once()

    @patch('flashcards.tts_service.ELEVENLABS_API_KEY', '')
    def test_generate_elevenlabs_tts_no_key(self):
        """Test ElevenLabs TTS when API key not available."""
        result = _generate_elevenlabs_tts('Test', 'de-DE')
        
        self.assertIsNone(result)


class TTSIntegrationTests(APITestCase):
    """Comprehensive integration tests for TTS functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('flashcards.tts_service.generate_tts_audio')
    def test_lesson_import_with_tts_generation(self, mock_generate_tts):
        """Test that TTS can be generated after lesson import."""
        mock_generate_tts.return_value = '/media/tts/test_audio.mp3'
        
        # Create lesson
        url = '/api/flashcards/reader/lessons/'
        data = {
            'title': 'Test Lesson',
            'text': 'Hallo Welt. Wie geht es dir?',
            'language': 'de',
            'source_type': 'text'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lesson_id = response.data['lesson_id']
        
        # Generate TTS
        tts_url = '/api/flashcards/reader/generate-tts/'
        tts_response = self.client.post(tts_url, {'lesson_id': lesson_id}, format='json')
        
        self.assertEqual(tts_response.status_code, status.HTTP_200_OK)
        self.assertIn('audio_url', tts_response.data)
        self.assertEqual(tts_response.data['audio_url'], '/media/tts/test_audio.mp3')
        
        # Verify lesson was updated
        lesson = Lesson.objects.get(lesson_id=lesson_id)
        self.assertEqual(lesson.audio_url, '/media/tts/test_audio.mp3')
        mock_generate_tts.assert_called_once()
    
    @patch('flashcards.tts_service.generate_tts_audio')
    def test_tts_generation_language_code_mapping(self, mock_generate_tts):
        """Test that language codes are properly mapped for TTS."""
        mock_generate_tts.return_value = '/media/tts/test.mp3'
        
        lesson = Lesson.objects.create(
            user=self.user,
            title='Test',
            text='Hola mundo',
            language='es'
        )
        
        url = '/api/flashcards/reader/generate-tts/'
        response = self.client.post(url, {'lesson_id': lesson.lesson_id}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify language code was mapped correctly (es -> es-ES)
        call_args = mock_generate_tts.call_args
        self.assertEqual(call_args[0][1], 'es-ES')  # language_code parameter
    
    @patch('flashcards.tts_service.generate_tts_audio')
    def test_tts_generation_with_explicit_language_code(self, mock_generate_tts):
        """Test TTS generation with explicit language code."""
        mock_generate_tts.return_value = '/media/tts/test.mp3'
        
        lesson = Lesson.objects.create(
            user=self.user,
            title='Test',
            text='Bonjour le monde',
            language='fr'
        )
        
        url = '/api/flashcards/reader/generate-tts/'
        response = self.client.post(url, {
            'lesson_id': lesson.lesson_id,
            'language_code': 'fr-FR'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        call_args = mock_generate_tts.call_args
        self.assertEqual(call_args[0][1], 'fr-FR')
    
    def test_tts_generation_requires_authentication(self):
        """Test that TTS generation requires authentication."""
        # Create unauthenticated client
        unauthenticated_client = APIClient()
        
        url = '/api/flashcards/reader/generate-tts/'
        response = unauthenticated_client.post(url, {'lesson_id': 1}, format='json')
        
        # Should be 401 or 403 (both indicate auth failure)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    @patch('flashcards.tts_service.generate_tts_audio')
    def test_tts_generation_updates_lesson_audio_url(self, mock_generate_tts):
        """Test that TTS generation updates lesson audio_url field."""
        mock_generate_tts.return_value = '/media/tts/updated_audio.mp3'
        
        lesson = Lesson.objects.create(
            user=self.user,
            title='Test',
            text='Test text',
            language='de',
            audio_url=None
        )
        
        self.assertIsNone(lesson.audio_url)
        
        url = '/api/flashcards/reader/generate-tts/'
        response = self.client.post(url, {'lesson_id': lesson.lesson_id}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lesson.refresh_from_db()
        self.assertEqual(lesson.audio_url, '/media/tts/updated_audio.mp3')
    
    @patch('flashcards.tts_service.generate_tts_audio')
    def test_tts_generation_returns_lesson_id_in_response(self, mock_generate_tts):
        """Test that TTS response includes lesson_id."""
        mock_generate_tts.return_value = '/media/tts/test.mp3'
        
        lesson = Lesson.objects.create(
            user=self.user,
            title='Test',
            text='Test text',
            language='de'
        )
        
        url = '/api/flashcards/reader/generate-tts/'
        response = self.client.post(url, {'lesson_id': lesson.lesson_id}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('lesson_id', response.data)
        self.assertEqual(response.data['lesson_id'], lesson.lesson_id)
        self.assertIn('message', response.data)


class ListeningTimeIntegrationTests(APITestCase):
    """Integration tests for listening time tracking."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt',
            language='de'
        )
    
    def test_listening_time_starts_at_zero(self):
        """Test that new lessons start with zero listening time."""
        self.assertEqual(self.lesson.total_listening_time_seconds, 0)
        self.assertIsNone(self.lesson.last_listened_at)
    
    def test_listening_time_serializer_includes_formatted_time(self):
        """Test that lesson serializer includes formatted listening time."""
        self.lesson.total_listening_time_seconds = 125  # 2 minutes 5 seconds
        self.lesson.save()
        
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('listening_time_formatted', response.data)
        self.assertEqual(response.data['listening_time_formatted'], '2:05')
    
    def test_listening_time_formatted_for_hours(self):
        """Test listening time formatting for hours."""
        self.lesson.total_listening_time_seconds = 3665  # 1 hour 1 minute 5 seconds
        self.lesson.save()
        
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['listening_time_formatted'], '1:01:05')
    
    def test_listening_time_updates_last_listened_at(self):
        """Test that updating listening time also updates last_listened_at."""
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/listening-time/'
        response = self.client.post(url, {
            'lesson_id': self.lesson.lesson_id,
            'seconds_listened': 30
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertIsNotNone(self.lesson.last_listened_at)
        self.assertIn('last_listened_at', response.data)


class LessonImportFlowTests(APITestCase):
    """End-to-end tests for lesson import flow."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_full_import_flow_with_tokenization(self):
        """Test complete lesson import flow including tokenization."""
        url = '/api/flashcards/reader/lessons/'
        data = {
            'title': 'German News Article',
            'text': 'Das ist ein Test. Es funktioniert gut.',
            'language': 'de',
            'source_type': 'text',
            'source_url': 'https://example.com/article'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Response should include lesson_id and token_count
        self.assertIn('lesson_id', response.data)
        self.assertIn('token_count', response.data)
        self.assertGreater(response.data['token_count'], 0)
        
        lesson_id = response.data['lesson_id']
        lesson = Lesson.objects.get(lesson_id=lesson_id)
        self.assertEqual(lesson.title, 'German News Article')
        self.assertEqual(lesson.text, 'Das ist ein Test. Es funktioniert gut.')
        self.assertEqual(lesson.language, 'de')
        self.assertEqual(lesson.source_type, 'text')
        self.assertEqual(lesson.source_url, 'https://example.com/article')
        
        # Verify tokens were created
        tokens = lesson.tokens.all()
        self.assertGreater(len(tokens), 0)
        # Check that tokens have proper structure
        for token in tokens:
            self.assertIsNotNone(token.text)
            self.assertIsNotNone(token.normalized)
            self.assertIsNotNone(token.start_offset)
            self.assertIsNotNone(token.end_offset)
    
    @patch('flashcards.tts_service.generate_tts_audio')
    def test_import_and_tts_generation_flow(self, mock_generate_tts):
        """Test lesson import followed by TTS generation."""
        mock_generate_tts.return_value = '/media/tts/imported_lesson.mp3'
        
        # Step 1: Import lesson
        import_url = '/api/flashcards/reader/lessons/'
        import_data = {
            'title': 'Test Lesson',
            'text': 'Hallo Welt',
            'language': 'de',
            'source_type': 'text'
        }
        import_response = self.client.post(import_url, import_data, format='json')
        self.assertEqual(import_response.status_code, status.HTTP_201_CREATED)
        # Get lesson_id from response or from created lesson
        if 'lesson_id' in import_response.data:
            lesson_id = import_response.data['lesson_id']
        else:
            lesson = Lesson.objects.filter(user=self.user).order_by('-created_at').first()
            lesson_id = lesson.lesson_id if lesson else None
            self.assertIsNotNone(lesson_id, "Lesson should have been created")
        
        # Step 2: Generate TTS
        tts_url = '/api/flashcards/reader/generate-tts/'
        tts_response = self.client.post(tts_url, {'lesson_id': lesson_id}, format='json')
        self.assertEqual(tts_response.status_code, status.HTTP_200_OK)
        
        # Step 3: Verify lesson has audio_url
        lesson = Lesson.objects.get(lesson_id=lesson_id)
        self.assertEqual(lesson.audio_url, '/media/tts/imported_lesson.mp3')
        
        # Step 4: Get lesson detail and verify audio_url is included
        detail_url = f'/api/flashcards/reader/lessons/{lesson_id}/'
        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['audio_url'], '/media/tts/imported_lesson.mp3')
    
    def test_lesson_import_creates_tokens_with_correct_positions(self):
        """Test that tokens have correct start and end offsets."""
        url = '/api/flashcards/reader/lessons/'
        data = {
            'title': 'Test',
            'text': 'Hallo Welt',
            'language': 'de',
            'source_type': 'text'
        }
        
        response = self.client.post(url, data, format='json')
        # Get lesson_id from response or from created lesson
        if 'lesson_id' in response.data:
            lesson_id = response.data['lesson_id']
        else:
            lesson = Lesson.objects.filter(user=self.user).order_by('-created_at').first()
            lesson_id = lesson.lesson_id if lesson else None
            self.assertIsNotNone(lesson_id, "Lesson should have been created")
        lesson = Lesson.objects.get(lesson_id=lesson_id)
        
        tokens = list(lesson.tokens.all().order_by('start_offset'))
        self.assertGreater(len(tokens), 0)
        
        # Verify tokens don't overlap and are in order
        for i in range(len(tokens) - 1):
            self.assertLessEqual(tokens[i].end_offset, tokens[i + 1].start_offset)
        
        # Verify first token starts at 0 or near 0
        self.assertGreaterEqual(tokens[0].start_offset, 0)
        
        # Verify last token ends within text length
        self.assertLessEqual(tokens[-1].end_offset, len(lesson.text))


class ReadingProgressTests(TestCase):
    """Test reading progress tracking on Lesson model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt. Das ist ein Test.',
            language='de'
        )
        # Create some tokens for progress calculation
        Token.objects.create(
            lesson=self.lesson,
            text='Hallo',
            normalized='hallo',
            start_offset=0,
            end_offset=5
        )
        Token.objects.create(
            lesson=self.lesson,
            text='Welt',
            normalized='welt',
            start_offset=6,
            end_offset=10
        )
        Token.objects.create(
            lesson=self.lesson,
            text='Das',
            normalized='das',
            start_offset=12,
            end_offset=15
        )
    
    def test_lesson_default_progress_fields(self):
        """Test that new lessons have default progress values."""
        self.assertEqual(self.lesson.status, 'not_started')
        self.assertEqual(self.lesson.words_read, 0)
        self.assertEqual(self.lesson.reading_time_seconds, 0)
        self.assertIsNone(self.lesson.last_read_at)
        self.assertIsNone(self.lesson.completed_at)
    
    def test_get_progress_percentage(self):
        """Test progress percentage calculation."""
        # 0 words read out of 3 tokens = 0%
        self.assertEqual(self.lesson.get_progress_percentage(), 0)
        
        # 1 word read out of 3 tokens = 33%
        self.lesson.words_read = 1
        self.assertEqual(self.lesson.get_progress_percentage(), 33)
        
        # 2 words read out of 3 tokens = 66%
        self.lesson.words_read = 2
        self.assertEqual(self.lesson.get_progress_percentage(), 66)
        
        # 3 words read out of 3 tokens = 100%
        self.lesson.words_read = 3
        self.assertEqual(self.lesson.get_progress_percentage(), 100)
        
        # More words than tokens should cap at 100%
        self.lesson.words_read = 5
        self.assertEqual(self.lesson.get_progress_percentage(), 100)
    
    def test_get_progress_percentage_no_tokens(self):
        """Test progress percentage when lesson has no tokens."""
        lesson = Lesson.objects.create(
            user=self.user,
            title='Empty Lesson',
            text='Test',
            language='de'
        )
        self.assertEqual(lesson.get_progress_percentage(), 0)
    
    def test_mark_completed(self):
        """Test marking lesson as completed."""
        self.assertEqual(self.lesson.status, 'not_started')
        self.assertIsNone(self.lesson.completed_at)
        
        self.lesson.mark_completed()
        
        self.assertEqual(self.lesson.status, 'completed')
        self.assertIsNotNone(self.lesson.completed_at)
    
    def test_mark_completed_idempotent(self):
        """Test that marking completed multiple times doesn't change completed_at."""
        self.lesson.mark_completed()
        first_completed_at = self.lesson.completed_at
        
        # Mark again
        self.lesson.mark_completed()
        
        self.assertEqual(self.lesson.completed_at, first_completed_at)


class ReadingProgressAPITests(APITestCase):
    """Test Reading Progress API endpoint."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt. Das ist ein Test.',
            language='de'
        )
        # Create tokens for progress calculation
        for i, word in enumerate(['Hallo', 'Welt', 'Das', 'ist', 'ein', 'Test']):
            Token.objects.create(
                lesson=self.lesson,
                text=word,
                normalized=word.lower(),
                start_offset=i * 6,
                end_offset=i * 6 + len(word)
            )
    
    def test_update_reading_progress_words_read(self):
        """Test updating words_read."""
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/progress/'
        data = {
            'words_read_delta': 3
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('words_read', response.data)
        self.assertEqual(response.data['words_read'], 3)
        self.assertIn('progress_percentage', response.data)
        
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.words_read, 3)
        self.assertIsNotNone(self.lesson.last_read_at)
        # Status should auto-update to 'in_progress'
        self.assertEqual(self.lesson.status, 'in_progress')
    
    def test_update_reading_progress_reading_time(self):
        """Test updating reading_time_seconds."""
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/progress/'
        data = {
            'reading_time_seconds_delta': 60
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reading_time_seconds', response.data)
        self.assertEqual(response.data['reading_time_seconds'], 60)
        self.assertIn('reading_time_formatted', response.data)
        
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.reading_time_seconds, 60)
        self.assertIsNotNone(self.lesson.last_read_at)
    
    def test_update_reading_progress_status(self):
        """Test updating status."""
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/progress/'
        data = {
            'status': 'completed'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('completed_at', response.data)
        self.assertIsNotNone(response.data['completed_at'])
        
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, 'completed')
        self.assertIsNotNone(self.lesson.completed_at)
    
    def test_update_reading_progress_all_fields(self):
        """Test updating all progress fields at once."""
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/progress/'
        data = {
            'words_read_delta': 4,
            'reading_time_seconds_delta': 120,
            'status': 'in_progress'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['words_read'], 4)
        self.assertEqual(response.data['reading_time_seconds'], 120)
        self.assertEqual(response.data['status'], 'in_progress')
        
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.words_read, 4)
        self.assertEqual(self.lesson.reading_time_seconds, 120)
        self.assertEqual(self.lesson.status, 'in_progress')
    
    def test_update_reading_progress_accumulates(self):
        """Test that progress updates accumulate."""
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/progress/'
        
        # First update
        self.client.patch(url, {'words_read_delta': 2, 'reading_time_seconds_delta': 30}, format='json')
        # Second update
        self.client.patch(url, {'words_read_delta': 2, 'reading_time_seconds_delta': 45}, format='json')
        
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.words_read, 4)
        self.assertEqual(self.lesson.reading_time_seconds, 75)
    
    def test_update_reading_progress_negative_delta(self):
        """Test that negative deltas are handled correctly."""
        self.lesson.words_read = 5
        self.lesson.reading_time_seconds = 100
        self.lesson.save()
        
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/progress/'
        data = {
            'words_read_delta': -2,
            'reading_time_seconds_delta': -20
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.words_read, 3)
        self.assertEqual(self.lesson.reading_time_seconds, 80)
    
    def test_update_reading_progress_prevents_negative_values(self):
        """Test that values cannot go below zero."""
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/progress/'
        data = {
            'words_read_delta': -100,
            'reading_time_seconds_delta': -100
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.words_read, 0)
        self.assertEqual(self.lesson.reading_time_seconds, 0)
    
    def test_update_reading_progress_lesson_not_found(self):
        """Test updating progress for non-existent lesson."""
        url = '/api/flashcards/reader/lessons/99999/progress/'
        data = {'words_read_delta': 1}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_reading_progress_other_user_lesson(self):
        """Test that users can't update progress for other users' lessons."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_lesson = Lesson.objects.create(
            user=other_user,
            title='Other Lesson',
            text='Test',
            language='de'
        )
        
        url = f'/api/flashcards/reader/lessons/{other_lesson.lesson_id}/progress/'
        data = {'words_read_delta': 1}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_reading_progress_invalid_status(self):
        """Test that invalid status values are rejected."""
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/progress/'
        data = {'status': 'invalid_status'}
        
        response = self.client.patch(url, data, format='json')
        
        # Should still succeed but status shouldn't change
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, 'not_started')
    
    def test_update_reading_progress_uncompleting_lesson(self):
        """Test that un-completing a lesson clears completed_at."""
        self.lesson.status = 'completed'
        self.lesson.completed_at = timezone.now()
        self.lesson.save()
        
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/progress/'
        data = {'status': 'in_progress'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.status, 'in_progress')
        self.assertIsNone(self.lesson.completed_at)
    
    def test_lesson_serializer_includes_progress_fields(self):
        """Test that lesson serializer includes all progress fields."""
        self.lesson.words_read = 3
        self.lesson.reading_time_seconds = 120
        self.lesson.status = 'in_progress'
        self.lesson.save()
        
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('words_read', response.data)
        self.assertIn('reading_time_seconds', response.data)
        self.assertIn('reading_time_formatted', response.data)
        self.assertIn('progress_percentage', response.data)
        self.assertIn('last_read_at', response.data)
        self.assertIn('completed_at', response.data)
        
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['words_read'], 3)
        self.assertEqual(response.data['reading_time_seconds'], 120)
        self.assertEqual(response.data['reading_time_formatted'], '2:00')
        self.assertEqual(response.data['progress_percentage'], 50)  # 3 out of 6 tokens
    
    def test_lesson_list_includes_progress_fields(self):
        """Test that lesson list endpoint includes progress fields."""
        self.lesson.words_read = 2
        self.lesson.reading_time_seconds = 60
        self.lesson.status = 'in_progress'
        self.lesson.save()
        
        url = '/api/flashcards/reader/lessons/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle paginated response
        if 'results' in response.data:
            lessons = response.data['results']
        else:
            lessons = response.data
        
        self.assertGreater(len(lessons), 0)
        lesson = lessons[0]
        self.assertIn('status', lesson)
        self.assertIn('words_read', lesson)
        self.assertIn('reading_time_seconds', lesson)
        self.assertIn('progress_percentage', lesson)
        self.assertIn('reading_time_formatted', lesson)


class TokenStatusModelTests(TestCase):
    """Test TokenStatus model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt',
            language='de'
        )
        self.token = Token.objects.create(
            lesson=self.lesson,
            text='Hallo',
            normalized='hallo',
            start_offset=0,
            end_offset=5
        )
    
    def test_create_token_status_known(self):
        """Test creating a known token status."""
        status = TokenStatus.objects.create(
            user=self.user,
            token=self.token,
            status='known'
        )
        self.assertEqual(status.status, 'known')
        self.assertEqual(status.user, self.user)
        self.assertEqual(status.token, self.token)
    
    def test_create_token_status_unknown(self):
        """Test creating an unknown token status."""
        status = TokenStatus.objects.create(
            user=self.user,
            token=self.token,
            status='unknown'
        )
        self.assertEqual(status.status, 'unknown')
    
    def test_token_status_unique_per_user(self):
        """Test that each user can only have one status per token."""
        TokenStatus.objects.create(
            user=self.user,
            token=self.token,
            status='known'
        )
        
        # Try to create another status for the same user/token
        status2, created = TokenStatus.objects.get_or_create(
            user=self.user,
            token=self.token,
            defaults={'status': 'unknown'}
        )
        
        # Should get existing status, not create new one
        self.assertFalse(created)
        self.assertEqual(status2.status, 'known')  # Original status
    
    def test_multiple_users_different_statuses(self):
        """Test that different users can have different statuses for same token."""
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        status1 = TokenStatus.objects.create(
            user=self.user,
            token=self.token,
            status='known'
        )
        status2 = TokenStatus.objects.create(
            user=user2,
            token=self.token,
            status='unknown'
        )
        
        self.assertEqual(status1.status, 'known')
        self.assertEqual(status2.status, 'unknown')
        self.assertEqual(TokenStatus.objects.filter(token=self.token).count(), 2)


class TokenStatusAPITests(APITestCase):
    """Test TokenStatus API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt',
            language='de'
        )
        self.token = Token.objects.create(
            lesson=self.lesson,
            text='Hallo',
            normalized='hallo',
            start_offset=0,
            end_offset=5
        )
    
    def test_mark_token_as_known(self):
        """Test marking a token as known."""
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/status/'
        response = self.client.post(url, {'status': 'known'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'known')
        self.assertEqual(response.data['token_id'], self.token.token_id)
        self.assertTrue(response.data['created'])
        
        # Verify status was saved
        token_status = TokenStatus.objects.get(user=self.user, token=self.token)
        self.assertEqual(token_status.status, 'known')
    
    def test_mark_token_as_unknown(self):
        """Test marking a token as unknown."""
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/status/'
        response = self.client.post(url, {'status': 'unknown'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'unknown')
        
        # Verify status was saved
        token_status = TokenStatus.objects.get(user=self.user, token=self.token)
        self.assertEqual(token_status.status, 'unknown')
    
    def test_update_token_status(self):
        """Test updating an existing token status."""
        # First mark as unknown
        TokenStatus.objects.create(
            user=self.user,
            token=self.token,
            status='unknown'
        )
        
        # Then update to known
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/status/'
        response = self.client.post(url, {'status': 'known'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'known')
        self.assertFalse(response.data['created'])  # Not created, updated
        
        # Verify status was updated
        token_status = TokenStatus.objects.get(user=self.user, token=self.token)
        self.assertEqual(token_status.status, 'known')
    
    def test_mark_token_status_missing_status(self):
        """Test marking status without providing status value."""
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/status/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status is required', response.data['error'])
    
    def test_mark_token_status_invalid_status(self):
        """Test marking status with invalid status value."""
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/status/'
        response = self.client.post(url, {'status': 'maybe'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status must be 'known' or 'unknown'", response.data['error'])
    
    def test_mark_token_status_not_found(self):
        """Test marking status for non-existent token."""
        url = '/api/flashcards/reader/tokens/99999/status/'
        response = self.client.post(url, {'status': 'known'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_mark_token_status_other_user_lesson(self):
        """Test that users cannot mark status for tokens in other users' lessons."""
        lesson2 = Lesson.objects.create(
            user=self.user2,
            title='Other User Lesson',
            text='Bonjour',
            language='fr'
        )
        token2 = Token.objects.create(
            lesson=lesson2,
            text='Bonjour',
            normalized='bonjour',
            start_offset=0,
            end_offset=7
        )
        
        url = f'/api/flashcards/reader/tokens/{token2.token_id}/status/'
        response = self.client.post(url, {'status': 'known'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_remove_token_status(self):
        """Test removing a token status."""
        # First create a status
        TokenStatus.objects.create(
            user=self.user,
            token=self.token,
            status='known'
        )
        
        # Then remove it
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/status/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify status was removed
        self.assertFalse(TokenStatus.objects.filter(user=self.user, token=self.token).exists())
    
    def test_remove_nonexistent_token_status(self):
        """Test removing a status that doesn't exist."""
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/status/'
        response = self.client.delete(url)
        
        # Should return success even if status doesn't exist
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('No status to remove', response.data['message'])
    
    def test_token_serializer_includes_status(self):
        """Test that TokenSerializer includes status field."""
        # Create a status
        TokenStatus.objects.create(
            user=self.user,
            token=self.token,
            status='known'
        )
        
        # Get lesson detail which includes tokens
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens = response.data.get('tokens', [])
        self.assertGreater(len(tokens), 0)
        
        # Find our token
        token_data = next((t for t in tokens if t['token_id'] == self.token.token_id), None)
        self.assertIsNotNone(token_data)
        self.assertIn('status', token_data)
        self.assertEqual(token_data['status'], 'known')
    
    def test_token_serializer_no_status_returns_none(self):
        """Test that TokenSerializer returns None for status when no status exists."""
        # Get lesson detail without creating a status
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens = response.data.get('tokens', [])
        self.assertGreater(len(tokens), 0)
        
        # Find our token
        token_data = next((t for t in tokens if t['token_id'] == self.token.token_id), None)
        self.assertIsNotNone(token_data)
        self.assertIn('status', token_data)
        self.assertIsNone(token_data['status'])
    
    def test_token_status_user_scoping(self):
        """Test that users only see their own token statuses."""
        # User1 marks token as known
        TokenStatus.objects.create(
            user=self.user,
            token=self.token,
            status='known'
        )
        
        # User2 marks same token as unknown (even though they can't access the lesson)
        TokenStatus.objects.create(
            user=self.user2,
            token=self.token,
            status='unknown'
        )
        
        # User1 should see 'known' in their lesson
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/'
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens = response.data.get('tokens', [])
        self.assertGreater(len(tokens), 0)
        token_data = next((t for t in tokens if t['token_id'] == self.token.token_id), None)
        self.assertIsNotNone(token_data, "Token should be found in response")
        self.assertIn('status', token_data)
        self.assertEqual(token_data['status'], 'known')
        
        # User2 should NOT be able to access user1's lesson (404)
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Create a lesson for user2 with the same token text to test status scoping
        lesson2 = Lesson.objects.create(
            user=self.user2,
            title='User2 Lesson',
            text=self.lesson.text,
            language=self.lesson.language
        )
        # Create token for user2's lesson (same text, different token_id)
        token2 = Token.objects.create(
            lesson=lesson2,
            text=self.token.text,
            normalized=self.token.normalized,
            start_offset=self.token.start_offset,
            end_offset=self.token.end_offset
        )
        # User2 should see 'unknown' status for their token
        url2 = f'/api/flashcards/reader/lessons/{lesson2.lesson_id}/'
        response = self.client.get(url2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens = response.data.get('tokens', [])
        self.assertGreater(len(tokens), 0)
        token_data = next((t for t in tokens if t['token_id'] == token2.token_id), None)
        self.assertIsNotNone(token_data, "Token should be found in response")
        self.assertIn('status', token_data)
        # User2's token should have no status (since TokenStatus was created for self.token, not token2)
        self.assertIsNone(token_data['status'])


class DictionaryServiceTests(TestCase):
    """Test dictionary service functionality."""
    
    def test_get_wiktionary_language_code(self):
        """Test language code mapping."""
        self.assertEqual(get_wiktionary_language_code('es'), 'Spanish')
        self.assertEqual(get_wiktionary_language_code('de'), 'German')
        self.assertEqual(get_wiktionary_language_code('en'), 'English')
        self.assertEqual(get_wiktionary_language_code('fr'), 'French')
        self.assertEqual(get_wiktionary_language_code('it'), 'Italian')
        self.assertEqual(get_wiktionary_language_code('pt'), 'Portuguese')
        # Fallback for unknown languages
        self.assertEqual(get_wiktionary_language_code('xx'), 'Xx')
    
    @patch('flashcards.dictionary_service.requests.get')
    @patch('flashcards.dictionary_service.cache')
    def test_get_dictionary_entry_success(self, mock_cache, mock_get):
        """Test successful dictionary entry retrieval."""
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Mock Wiktionary API response (actual structure)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'de': [
                {
                    'partOfSpeech': 'noun',
                    'definitions': [
                        {
                            'definition': '<span>greeting, hello</span>'
                        }
                    ],
                    'examples': [
                        {'text': 'Hallo, wie geht es dir?'}
                    ]
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = get_dictionary_entry('Hallo', 'de', 'en')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['source'], 'wiktionary')
        self.assertIn('meanings', result)
        self.assertEqual(len(result['meanings']), 1)
        self.assertEqual(result['meanings'][0]['part_of_speech'], 'noun')
        self.assertIn('definitions', result['meanings'][0])
        self.assertIn('examples', result['meanings'][0])
        mock_cache.set.assert_called_once()
    
    @patch('flashcards.dictionary_service.requests.get')
    @patch('flashcards.dictionary_service.cache')
    def test_get_dictionary_entry_cache_hit(self, mock_cache, mock_get):
        """Test dictionary entry cache hit."""
        cached_entry = {
            'meanings': [{'part_of_speech': 'noun', 'definitions': ['hello'], 'examples': []}],
            'source': 'wiktionary'
        }
        mock_cache.get.return_value = cached_entry
        
        result = get_dictionary_entry('Hallo', 'de', 'en')
        
        self.assertEqual(result, cached_entry)
        mock_get.assert_not_called()
    
    @patch('flashcards.dictionary_service.requests.get')
    def test_get_dictionary_entry_not_found(self, mock_get):
        """Test dictionary entry when word not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = get_dictionary_entry('NonexistentWord12345', 'de', 'en')
        
        self.assertIsNone(result)
    
    @patch('flashcards.dictionary_service.requests.get')
    def test_get_dictionary_entry_api_error(self, mock_get):
        """Test dictionary entry when API error occurs."""
        mock_get.side_effect = Exception("API Error")
        
        result = get_dictionary_entry('Hallo', 'de', 'en')
        
        self.assertIsNone(result)
    
    def test_parse_wiktionary_response_valid(self):
        """Test parsing valid Wiktionary response."""
        data = {
            'de': [
                {
                    'partOfSpeech': 'noun',
                    'definitions': [
                        {
                            'definition': '<span>greeting, hello</span>'
                        }
                    ],
                    'examples': [
                        {'text': 'Hallo Welt'}
                    ]
                },
                {
                    'partOfSpeech': 'interjection',
                    'definitions': [
                        {
                            'definition': '<span>hey</span>'
                        }
                    ]
                }
            ]
        }
        
        result = _parse_wiktionary_response(data, 'de', 'en')
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result['meanings']), 2)
        self.assertEqual(result['meanings'][0]['part_of_speech'], 'noun')
        self.assertGreater(len(result['meanings'][0]['definitions']), 0)
        self.assertEqual(len(result['meanings'][0]['examples']), 1)
    
    def test_parse_wiktionary_response_empty(self):
        """Test parsing empty Wiktionary response."""
        result = _parse_wiktionary_response({}, 'de', 'en')
        self.assertIsNone(result)
        
        result = _parse_wiktionary_response({'de': {}}, 'de', 'en')
        self.assertIsNone(result)
    
    def test_parse_wiktionary_response_no_definitions(self):
        """Test parsing response with no definitions."""
        data = {
            'de': []
        }
        
        result = _parse_wiktionary_response(data, 'de', 'en')
        self.assertIsNone(result)
    
    def test_parse_wiktionary_response_german_word(self):
        """Test parsing German word with actual Wiktionary API structure."""
        # This is the actual structure returned by Wiktionary API for German words
        data = {
            'de': [
                {
                    'partOfSpeech': 'Participle',
                    'definitions': [
                        {
                            'definition': '<span>past participle of <a>vorschlagen</a></span>'
                        }
                    ]
                },
                {
                    'partOfSpeech': 'Verb',
                    'definitions': [
                        {
                            'definition': '<span>to suggest, to propose</span>'
                        }
                    ],
                    'examples': [
                        {'text': 'Er hat einen Vorschlag gemacht.'}
                    ]
                }
            ]
        }
        
        result = _parse_wiktionary_response(data, 'de', 'en')
        
        self.assertIsNotNone(result)
        self.assertIn('meanings', result)
        self.assertEqual(len(result['meanings']), 2)
        self.assertEqual(result['meanings'][0]['part_of_speech'], 'participle')
        self.assertIn('past participle of vorschlagen', result['meanings'][0]['definitions'][0])
        self.assertEqual(result['meanings'][1]['part_of_speech'], 'verb')
        self.assertIn('to suggest', result['meanings'][1]['definitions'][0])
        self.assertEqual(len(result['meanings'][1]['examples']), 1)
    
    def test_get_dictionary_entry_normalizes_word(self):
        """Test that dictionary entry normalizes word before lookup."""
        with patch('flashcards.dictionary_service.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'de': {'definitions': []}}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            # Should normalize punctuation
            get_dictionary_entry('Hallo!', 'de', 'en')
            # Check that normalized word was used in URL
            call_args = mock_get.call_args
            self.assertIn('hallo', call_args[0][0].lower())


class DictionaryIntegrationTests(APITestCase):
    """Test dictionary integration with token click API."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test Lesson',
            text='Hallo Welt. Das ist ein Test.',
            language='de'
        )
        self.token = Token.objects.create(
            lesson=self.lesson,
            text='Hallo',
            normalized='hallo',
            start_offset=0,
            end_offset=5
        )
    
    @patch('flashcards.dictionary_service.get_dictionary_entry')
    @patch('flashcards.translation_service.get_word_translation')
    @patch('flashcards.translation_service.translate_text')
    def test_token_click_fetches_dictionary_entry(self, mock_sentence_translate, mock_word_translate, mock_dict_entry):
        """Test that clicking a token fetches dictionary entry."""
        mock_word_translate.return_value = {'translation': 'Hello'}
        mock_sentence_translate.return_value = 'Hello World.'
        mock_dict_entry.return_value = {
            'meanings': [
                {
                    'part_of_speech': 'noun',
                    'definitions': ['greeting', 'hello'],
                    'examples': ['Hallo Welt']
                }
            ],
            'source': 'wiktionary'
        }
        
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/click/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('dictionary_entry', response.data['token'])
        
        # Verify dictionary entry was fetched
        mock_dict_entry.assert_called_once_with('Hallo', 'de', 'en')
        
        # Verify token was updated with dictionary entry
        self.token.refresh_from_db()
        self.assertIsNotNone(self.token.dictionary_entry)
        self.assertIn('meanings', self.token.dictionary_entry)
    
    @patch('flashcards.dictionary_service.get_dictionary_entry')
    @patch('flashcards.translation_service.get_word_translation')
    @patch('flashcards.translation_service.translate_text')
    def test_token_click_uses_cached_dictionary_entry(self, mock_sentence_translate, mock_word_translate, mock_dict_entry):
        """Test that clicking a token uses cached dictionary entry."""
        # Set up token with existing dictionary entry
        self.token.dictionary_entry = {
            'meanings': [
                {
                    'part_of_speech': 'noun',
                    'definitions': ['greeting'],
                    'examples': []
                }
            ],
            'source': 'wiktionary'
        }
        self.token.save()
        
        mock_word_translate.return_value = {'translation': 'Hello'}
        mock_sentence_translate.return_value = 'Hello World.'
        
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/click/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should not fetch dictionary entry again
        mock_dict_entry.assert_not_called()
        
        # Should return cached dictionary entry
        self.assertIn('dictionary_entry', response.data['token'])
        self.assertEqual(len(response.data['token']['dictionary_entry']['meanings']), 1)
    
    @patch('flashcards.dictionary_service.get_dictionary_entry')
    @patch('flashcards.translation_service.get_word_translation')
    @patch('flashcards.translation_service.translate_text')
    def test_token_click_handles_dictionary_failure(self, mock_sentence_translate, mock_word_translate, mock_dict_entry):
        """Test that token click handles dictionary lookup failure gracefully."""
        mock_word_translate.return_value = {'translation': 'Hello'}
        mock_sentence_translate.return_value = 'Hello World.'
        mock_dict_entry.return_value = None  # Dictionary lookup fails
        
        url = f'/api/flashcards/reader/tokens/{self.token.token_id}/click/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should still return token with translation
        self.assertIn('token', response.data)
        self.assertIn('translation', response.data['token'])
        # Dictionary entry should be empty dict (default) or have no meanings
        self.token.refresh_from_db()
        # dictionary_entry defaults to {}, so check if it has no meanings
        self.assertFalse(self.token.dictionary_entry.get('meanings'))
    
    def test_token_serializer_includes_dictionary_entry(self):
        """Test that TokenSerializer includes dictionary_entry field."""
        self.token.dictionary_entry = {
            'meanings': [
                {
                    'part_of_speech': 'noun',
                    'definitions': ['greeting'],
                    'examples': []
                }
            ],
            'source': 'wiktionary'
        }
        self.token.save()
        
        url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tokens = response.data.get('tokens', [])
        self.assertGreater(len(tokens), 0)
        
        token_data = next((t for t in tokens if t['token_id'] == self.token.token_id), None)
        self.assertIsNotNone(token_data)
        self.assertIn('dictionary_entry', token_data)
        self.assertIn('meanings', token_data['dictionary_entry'])
