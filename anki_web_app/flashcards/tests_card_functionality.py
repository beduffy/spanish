"""
Comprehensive tests for Card functionality with test user.
Tests: create, read, update, delete, review, import, statistics
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
import json

from flashcards.models import Card, CardReview, GRADUATING_INTERVAL_DAYS

User = get_user_model()


class CardFunctionalityTestCase(TestCase):
    """Test all card functionality with authenticated test user."""

    def setUp(self):
        """Set up test user and API client."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = APIClient()
        # Simulate authentication by setting user directly
        self.client.force_authenticate(user=self.user)
        self.today = timezone.now().date()

    def test_create_card(self):
        """Test creating a new card."""
        data = {
            'front': 'Hello',
            'back': 'Hola',
            'notes': 'Test card',
            'tags': ['greeting', 'basic'],
            'create_reverse': True
        }
        response = self.client.post('/api/flashcards/cards/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Card.objects.filter(user=self.user).count(), 2)  # Forward + reverse
        card = Card.objects.get(front='Hello', user=self.user)
        self.assertEqual(card.back, 'Hola')
        self.assertEqual(card.notes, 'Test card')
        self.assertTrue(card.is_learning)
        self.assertEqual(card.interval_days, 0)
        self.assertEqual(card.next_review_date, self.today)

    def test_create_card_without_reverse(self):
        """Test creating a card without reverse."""
        data = {
            'front': 'Goodbye',
            'back': 'Adiós',
            'create_reverse': False
        }
        response = self.client.post('/api/flashcards/cards/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Card.objects.filter(user=self.user).count(), 1)
        card = Card.objects.get(front='Goodbye', user=self.user)
        self.assertIsNone(card.linked_card)

    def test_get_all_cards(self):
        """Test retrieving all cards."""
        # Create test cards
        Card.objects.create(
            user=self.user,
            front='Card 1',
            back='Tarjeta 1',
            next_review_date=self.today
        )
        Card.objects.create(
            user=self.user,
            front='Card 2',
            back='Tarjeta 2',
            next_review_date=self.today
        )
        
        response = self.client.get('/api/flashcards/cards/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_card_details(self):
        """Test retrieving a specific card."""
        card = Card.objects.create(
            user=self.user,
            front='Test Card',
            back='Tarjeta de Prueba',
            notes='Test notes',
            tags=['test'],
            next_review_date=self.today
        )
        
        response = self.client.get(f'/api/flashcards/cards/{card.card_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['front'], 'Test Card')
        self.assertEqual(response.data['back'], 'Tarjeta de Prueba')
        self.assertEqual(response.data['notes'], 'Test notes')

    def test_update_card(self):
        """Test updating a card."""
        card = Card.objects.create(
            user=self.user,
            front='Original',
            back='Original Back',
            next_review_date=self.today
        )
        
        data = {
            'front': 'Updated',
            'back': 'Updated Back',
            'notes': 'Updated notes',
            'tags': ['updated']
        }
        response = self.client.put(
            f'/api/flashcards/cards/{card.card_id}/update/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertEqual(card.front, 'Updated')
        self.assertEqual(card.back, 'Updated Back')
        self.assertEqual(card.notes, 'Updated notes')

    def test_delete_card(self):
        """Test deleting a card."""
        card = Card.objects.create(
            user=self.user,
            front='To Delete',
            back='Eliminar',
            next_review_date=self.today
        )
        card_id = card.card_id
        
        response = self.client.delete(f'/api/flashcards/cards/{card_id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Card.objects.filter(card_id=card_id).exists())

    def test_delete_card_with_linked_reverse(self):
        """Test deleting a card also deletes its linked reverse card."""
        forward = Card.objects.create(
            user=self.user,
            front='Forward',
            back='Backward',
            next_review_date=self.today
        )
        reverse = Card.objects.create(
            user=self.user,
            front='Backward',
            back='Forward',
            pair_id=forward.pair_id,
            linked_card=forward,
            next_review_date=self.today
        )
        forward.linked_card = reverse
        forward.save()
        
        forward_id = forward.card_id
        reverse_id = reverse.card_id
        
        response = self.client.delete(f'/api/flashcards/cards/{forward_id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Card.objects.filter(card_id=forward_id).exists())
        self.assertFalse(Card.objects.filter(card_id=reverse_id).exists())

    def test_get_next_card(self):
        """Test getting the next card for review."""
        # Create cards due for review
        Card.objects.create(
            user=self.user,
            front='Due Card',
            back='Tarjeta Debida',
            next_review_date=self.today,
            is_learning=False,
            interval_days=5
        )
        Card.objects.create(
            user=self.user,
            front='Future Card',
            back='Tarjeta Futura',
            next_review_date=self.today + timedelta(days=5),
            is_learning=False,
            interval_days=10
        )
        
        response = self.client.get('/api/flashcards/cards/next-card/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['front'], 'Due Card')

    def test_get_next_card_prioritizes_review_over_learning(self):
        """Test that review cards are prioritized over learning cards."""
        # Create a learning card due today
        Card.objects.create(
            user=self.user,
            front='Learning Card',
            back='Tarjeta de Aprendizaje',
            next_review_date=self.today,
            is_learning=True,
            interval_days=0
        )
        # Create a review card due today
        Card.objects.create(
            user=self.user,
            front='Review Card',
            back='Tarjeta de Revisión',
            next_review_date=self.today,
            is_learning=False,
            interval_days=5
        )
        
        response = self.client.get('/api/flashcards/cards/next-card/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['front'], 'Review Card')

    def test_submit_card_review(self):
        """Test submitting a review for a card."""
        card = Card.objects.create(
            user=self.user,
            front='Review Me',
            back='Revisame',
            next_review_date=self.today,
            is_learning=True,
            interval_days=0
        )
        
        data = {
            'card_id': card.card_id,
            'user_score': 0.9,
            'user_comment_addon': 'Great!',
            'typed_input': 'Revisame'
        }
        response = self.client.post('/api/flashcards/cards/submit-review/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        card.refresh_from_db()
        self.assertEqual(card.total_reviews, 1)
        self.assertEqual(card.total_score_sum, 0.9)
        self.assertEqual(card.consecutive_correct_reviews, 1)
        
        # Check review was created
        review = CardReview.objects.get(card=card)
        self.assertEqual(review.user_score, 0.9)
        self.assertEqual(review.user_comment_addon, 'Great!')
        self.assertEqual(review.typed_input, 'Revisame')

    def test_submit_review_graduation(self):
        """Test that submitting reviews can graduate a card from learning."""
        from flashcards.models import LEARNING_STEPS_DAYS
        
        card = Card.objects.create(
            user=self.user,
            front='Learning Card',
            back='Tarjeta de Aprendizaje',
            next_review_date=self.today,
            is_learning=True,
            interval_days=0
        )
        
        # First review: score 0.9 (should move to first learning step: 1 day)
        data = {'card_id': card.card_id, 'user_score': 0.9}
        self.client.post('/api/flashcards/cards/submit-review/', data, format='json')
        card.refresh_from_db()
        self.assertTrue(card.is_learning)
        self.assertEqual(card.interval_days, LEARNING_STEPS_DAYS[0])
        
        # Second review: score 0.9 (should move to second learning step: 3 days)
        card.next_review_date = self.today
        card.save()
        self.client.post('/api/flashcards/cards/submit-review/', data, format='json')
        card.refresh_from_db()
        self.assertTrue(card.is_learning)
        self.assertEqual(card.interval_days, LEARNING_STEPS_DAYS[1])
        
        # Third review: score 0.9 (should graduate)
        card.next_review_date = self.today
        card.save()
        self.client.post('/api/flashcards/cards/submit-review/', data, format='json')
        card.refresh_from_db()
        self.assertFalse(card.is_learning)
        self.assertEqual(card.interval_days, GRADUATING_INTERVAL_DAYS)

    def test_card_statistics(self):
        """Test card statistics endpoint."""
        # Create cards with reviews
        card1 = Card.objects.create(
            user=self.user,
            front='Card 1',
            back='Tarjeta 1',
            next_review_date=self.today
        )
        card2 = Card.objects.create(
            user=self.user,
            front='Card 2',
            back='Tarjeta 2',
            next_review_date=self.today
        )
        
        # Create reviews
        CardReview.objects.create(
            card=card1,
            user_score=0.9,
            review_timestamp=timezone.now(),
            interval_at_review=0,
            ease_factor_at_review=2.5
        )
        CardReview.objects.create(
            card=card1,
            user_score=0.8,
            review_timestamp=timezone.now(),
            interval_at_review=1,
            ease_factor_at_review=2.5
        )
        
        response = self.client.get('/api/flashcards/cards/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_cards'], 2)
        self.assertEqual(response.data['reviews_today'], 2)
        self.assertEqual(response.data['total_reviews_all_time'], 2)
        self.assertIsNotNone(response.data['overall_average_score'])

    def test_user_isolation(self):
        """Test that users only see their own cards."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass'
        )
        
        # Create cards for both users
        Card.objects.create(
            user=self.user,
            front='My Card',
            back='Mi Tarjeta',
            next_review_date=self.today
        )
        Card.objects.create(
            user=other_user,
            front='Other Card',
            back='Otra Tarjeta',
            next_review_date=self.today
        )
        
        response = self.client.get('/api/flashcards/cards/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['front'], 'My Card')

    def test_mastery_level_calculation(self):
        """Test that mastery level is calculated correctly."""
        # New card (no reviews)
        new_card = Card.objects.create(
            user=self.user,
            front='New',
            back='Nuevo',
            next_review_date=self.today,
            total_reviews=0
        )
        
        # Mastered card
        mastered_card = Card.objects.create(
            user=self.user,
            front='Mastered',
            back='Dominado',
            next_review_date=self.today,
            is_learning=False,
            interval_days=GRADUATING_INTERVAL_DAYS,
            consecutive_correct_reviews=3,
            total_reviews=5,
            total_score_sum=4.5  # Average 0.9
        )
        
        response = self.client.get('/api/flashcards/cards/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Find cards in response
        new_card_data = next(c for c in response.data['results'] if c['front'] == 'New')
        mastered_card_data = next(c for c in response.data['results'] if c['front'] == 'Mastered')
        
        self.assertEqual(new_card_data['mastery_level']['level'], 'New')
        # Check mastery level exists and has correct structure
        self.assertIn('mastery_level', mastered_card_data)
        self.assertEqual(mastered_card_data['mastery_level']['level'], 'Mastered')

    def test_card_pagination(self):
        """Test that card list pagination works."""
        # Create more than one page of cards
        for i in range(25):
            Card.objects.create(
                user=self.user,
                front=f'Card {i}',
                back=f'Tarjeta {i}',
                next_review_date=self.today
            )
        
        response = self.client.get('/api/flashcards/cards/?page=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check pagination structure exists
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(response.data['count'], 25)
        
        # Check that we can get page 2 if it exists
        if response.data.get('total_pages', 0) > 1:
            response2 = self.client.get('/api/flashcards/cards/?page=2')
            self.assertEqual(response2.status_code, status.HTTP_200_OK)
            self.assertIn('results', response2.data)
