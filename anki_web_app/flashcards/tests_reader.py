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
from flashcards.models import Lesson, Token, Phrase, Card
from flashcards.tokenization import tokenize_text, normalize_token
from flashcards.translation_service import translate_text, get_word_translation
from flashcards.tts_service import generate_tts_audio, _generate_google_tts, _generate_elevenlabs_tts

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
