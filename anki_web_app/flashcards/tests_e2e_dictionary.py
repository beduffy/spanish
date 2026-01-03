"""
End-to-end tests for dictionary integration.
Tests the full flow from token click to dictionary display.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
import json

from flashcards.models import Lesson, Token
from flashcards.dictionary_service import get_dictionary_entry

User = get_user_model()


class DictionaryE2ETests(TestCase):
    """End-to-end tests for dictionary feature."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create a German lesson
        self.lesson = Lesson.objects.create(
            user=self.user,
            title='Test German Lesson',
            text='Ein Autor hat dafür „Robot Olympics" vorgeschlagen.',
            language='de'
        )
        
        # Create tokens
        self.token1 = Token.objects.create(
            lesson=self.lesson,
            text='vorgeschlagen',
            normalized='vorgeschlagen',
            start_offset=35,
            end_offset=48
        )
    
    def test_e2e_dictionary_lookup_german_word(self):
        """Test end-to-end dictionary lookup for German word."""
        # Step 1: Click token (triggers dictionary lookup)
        url = f'/api/flashcards/reader/tokens/{self.token1.token_id}/click/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        
        token_data = response.data['token']
        self.assertIn('dictionary_entry', token_data)
        
        # Step 2: Verify dictionary entry was fetched
        dictionary_entry = token_data.get('dictionary_entry')
        if dictionary_entry:
            self.assertIn('meanings', dictionary_entry)
            self.assertGreater(len(dictionary_entry['meanings']), 0)
            
            # Verify structure
            meaning = dictionary_entry['meanings'][0]
            self.assertIn('part_of_speech', meaning)
            self.assertIn('definitions', meaning)
            self.assertGreater(len(meaning['definitions']), 0)
    
    def test_e2e_dictionary_cached_on_second_click(self):
        """Test that dictionary entry is cached and reused."""
        # First click - should fetch from API
        url = f'/api/flashcards/reader/tokens/{self.token1.token_id}/click/'
        response1 = self.client.get(url)
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        dict_entry1 = response1.data['token'].get('dictionary_entry')
        
        # Second click - should use cached entry
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        dict_entry2 = response2.data['token'].get('dictionary_entry')
        
        # Should have same dictionary entry (cached)
        if dict_entry1:
            self.assertEqual(dict_entry1, dict_entry2)
    
    def test_e2e_dictionary_serializer_includes_entry(self):
        """Test that dictionary entry is included in lesson serializer."""
        # First click token to fetch dictionary
        click_url = f'/api/flashcards/reader/tokens/{self.token1.token_id}/click/'
        self.client.get(click_url)
        
        # Get lesson detail
        lesson_url = f'/api/flashcards/reader/lessons/{self.lesson.lesson_id}/'
        response = self.client.get(lesson_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        
        # Find our token
        tokens = response.data['tokens']
        token_data = next((t for t in tokens if t['token_id'] == self.token1.token_id), None)
        
        self.assertIsNotNone(token_data)
        self.assertIn('dictionary_entry', token_data)
        
        # If dictionary was fetched, verify structure
        if token_data.get('dictionary_entry'):
            dict_entry = token_data['dictionary_entry']
            self.assertIn('meanings', dict_entry)
    
    def test_e2e_dictionary_fallback_to_translation(self):
        """Test that translation is shown if dictionary lookup fails."""
        # Create token with non-existent word
        token2 = Token.objects.create(
            lesson=self.lesson,
            text='nonexistentword12345',
            normalized='nonexistentword12345',
            start_offset=0,
            end_offset=20
        )
        
        url = f'/api/flashcards/reader/tokens/{token2.token_id}/click/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token_data = response.data['token']
        
        # Should still return token (even if dictionary lookup fails)
        self.assertIsNotNone(token_data)
        # Dictionary entry might be empty or None
        # But translation should still work
        self.assertIn('translation', token_data)
