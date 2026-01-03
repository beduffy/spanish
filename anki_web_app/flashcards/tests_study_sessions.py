"""
Comprehensive tests for Study Session functionality.
Tests: model methods, API endpoints, AFK detection, active time calculation
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import timedelta

from flashcards.models import StudySession, SessionActivity, Card, CardReview

User = get_user_model()


class StudySessionModelTests(TestCase):
    """Test StudySession model methods."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_session(self):
        """Test creating a study session."""
        session = StudySession.objects.create(user=self.user)
        
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.user, self.user)
        self.assertTrue(session.is_active)
        self.assertIsNone(session.end_time)
        self.assertIsNotNone(session.start_time)
        self.assertIsNotNone(session.last_activity_time)

    def test_record_activity(self):
        """Test recording activity updates last_activity_time."""
        session = StudySession.objects.create(user=self.user)
        original_time = session.last_activity_time
        
        # Wait a moment
        import time
        time.sleep(0.1)
        
        session.record_activity()
        session.refresh_from_db()
        
        self.assertGreater(session.last_activity_time, original_time)

    def test_record_activity_inactive_session(self):
        """Test that recording activity on inactive session doesn't update."""
        session = StudySession.objects.create(user=self.user)
        session.end_session()
        original_time = session.last_activity_time
        
        import time
        time.sleep(0.1)
        
        session.record_activity()
        session.refresh_from_db()
        
        # Should not update for inactive session
        self.assertEqual(session.last_activity_time, original_time)

    def test_end_session(self):
        """Test ending a session."""
        session = StudySession.objects.create(user=self.user)
        self.assertTrue(session.is_active)
        self.assertIsNone(session.end_time)
        
        session.end_session()
        
        self.assertFalse(session.is_active)
        self.assertIsNotNone(session.end_time)

    def test_end_session_idempotent(self):
        """Test that ending a session multiple times doesn't change end_time."""
        session = StudySession.objects.create(user=self.user)
        session.end_session()
        first_end_time = session.end_time
        
        session.end_session()
        session.refresh_from_db()
        
        self.assertEqual(session.end_time, first_end_time)

    def test_calculate_active_minutes_no_activities(self):
        """Test active minutes calculation with no activities."""
        session = StudySession.objects.create(user=self.user)
        
        # End session immediately
        session.end_session()
        
        active_minutes = session.calculate_active_minutes()
        
        # Should be very small (just creation to end)
        self.assertGreaterEqual(active_minutes, 0)

    def test_calculate_active_minutes_with_activities(self):
        """Test active minutes calculation with activities."""
        session = StudySession.objects.create(user=self.user)
        start_time = session.start_time
        
        # Create activities within threshold (60 seconds apart)
        for i in range(3):
            activity_time = start_time + timedelta(seconds=30 * (i + 1))
            SessionActivity.objects.create(
                session=session,
                timestamp=activity_time
            )
        
        # End session
        end_time = start_time + timedelta(seconds=120)
        session.end_time = end_time
        session.is_active = False
        session.save()
        
        active_minutes = session.calculate_active_minutes()
        
        # Should be approximately 2 minutes (120 seconds / 60)
        self.assertAlmostEqual(active_minutes, 2.0, delta=0.1)

    def test_calculate_active_minutes_afk_detection(self):
        """Test that AFK gaps are excluded from active time."""
        session = StudySession.objects.create(user=self.user)
        start_time = session.start_time
        
        # Create activity at 30 seconds
        SessionActivity.objects.create(
            session=session,
            timestamp=start_time + timedelta(seconds=30)
        )
        
        # Large gap (AFK) - 200 seconds (exceeds 90 second threshold)
        SessionActivity.objects.create(
            session=session,
            timestamp=start_time + timedelta(seconds=230)
        )
        
        # End session at 250 seconds
        session.end_time = start_time + timedelta(seconds=250)
        session.is_active = False
        session.save()
        
        active_minutes = session.calculate_active_minutes()
        
        # Should only count: 0-30s (30s) + 230-250s (20s) = 50s = ~0.83 minutes
        # The gap from 30-230s should be excluded
        self.assertAlmostEqual(active_minutes, 0.83, delta=0.1)

    def test_calculate_active_minutes_custom_threshold(self):
        """Test active minutes with custom AFK threshold."""
        session = StudySession.objects.create(user=self.user)
        start_time = session.start_time
        
        # Create activity at 30 seconds
        SessionActivity.objects.create(
            session=session,
            timestamp=start_time + timedelta(seconds=30)
        )
        
        # Gap of 100 seconds (exceeds default 90s threshold)
        SessionActivity.objects.create(
            session=session,
            timestamp=start_time + timedelta(seconds=130)
        )
        
        session.end_time = start_time + timedelta(seconds=150)
        session.is_active = False
        session.save()
        
        # With default threshold (90s), gap should be excluded
        active_default = session.calculate_active_minutes()
        
        # With custom threshold (120s), gap should be included
        active_custom = session.calculate_active_minutes(afk_threshold_seconds=120)
        
        self.assertLess(active_default, active_custom)

    def test_calculate_active_minutes_active_session(self):
        """Test active minutes calculation for active session."""
        session = StudySession.objects.create(user=self.user)
        start_time = session.start_time
        
        # Create some activities
        for i in range(2):
            SessionActivity.objects.create(
                session=session,
                timestamp=start_time + timedelta(seconds=30 * (i + 1))
            )
        
        # Calculate for active session (uses timezone.now() as end)
        active_minutes = session.calculate_active_minutes()
        
        # Should be at least the time from start to last activity
        self.assertGreaterEqual(active_minutes, 0)


class StudySessionAPITests(APITestCase):
    """Test Study Session API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        StudySession.objects.all().delete()
        SessionActivity.objects.all().delete()

    def test_start_session(self):
        """Test starting a new study session."""
        url = '/api/flashcards/sessions/start/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('session_id', response.data)
        self.assertIn('start_time', response.data)
        
        # Verify session was created
        session = StudySession.objects.get(session_id=response.data['session_id'])
        self.assertEqual(session.user, self.user)
        self.assertTrue(session.is_active)

    def test_start_multiple_sessions(self):
        """Test that multiple sessions can be started."""
        url = '/api/flashcards/sessions/start/'
        
        response1 = self.client.post(url)
        response2 = self.client.post(url)
        
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        self.assertNotEqual(response1.data['session_id'], response2.data['session_id'])
        self.assertEqual(StudySession.objects.filter(user=self.user).count(), 2)

    def test_heartbeat_success(self):
        """Test sending heartbeat for active session."""
        session = StudySession.objects.create(user=self.user)
        original_time = session.last_activity_time
        
        url = '/api/flashcards/sessions/heartbeat/'
        response = self.client.post(url, {'session_id': session.session_id}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertIn('last_activity_time', response.data)
        
        # Verify activity was recorded
        session.refresh_from_db()
        self.assertGreater(session.last_activity_time, original_time)
        self.assertEqual(SessionActivity.objects.filter(session=session).count(), 1)

    def test_heartbeat_missing_session_id(self):
        """Test heartbeat without session_id."""
        url = '/api/flashcards/sessions/heartbeat/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_heartbeat_inactive_session(self):
        """Test heartbeat for inactive session."""
        session = StudySession.objects.create(user=self.user)
        session.end_session()
        
        url = '/api/flashcards/sessions/heartbeat/'
        response = self.client.post(url, {'session_id': session.session_id}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_heartbeat_other_user_session(self):
        """Test that users can't heartbeat other users' sessions."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_session = StudySession.objects.create(user=other_user)
        
        url = '/api/flashcards/sessions/heartbeat/'
        response = self.client.post(url, {'session_id': other_session.session_id}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_end_session_success(self):
        """Test ending a session."""
        session = StudySession.objects.create(user=self.user)
        
        # Add some activities
        for i in range(2):
            SessionActivity.objects.create(
                session=session,
                timestamp=timezone.now() - timedelta(seconds=60 - i * 10)
            )
        
        url = '/api/flashcards/sessions/end/'
        response = self.client.post(url, {'session_id': session.session_id}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('session_id', response.data)
        self.assertIn('start_time', response.data)
        self.assertIn('end_time', response.data)
        self.assertIn('active_minutes', response.data)
        
        # Verify session was ended
        session.refresh_from_db()
        self.assertFalse(session.is_active)
        self.assertIsNotNone(session.end_time)

    def test_end_session_missing_session_id(self):
        """Test ending session without session_id."""
        url = '/api/flashcards/sessions/end/'
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_end_session_already_ended(self):
        """Test ending an already ended session."""
        session = StudySession.objects.create(user=self.user)
        session.end_session()
        
        url = '/api/flashcards/sessions/end/'
        response = self.client.post(url, {'session_id': session.session_id}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_sessions(self):
        """Test listing all sessions for user."""
        # Create multiple sessions
        session1 = StudySession.objects.create(user=self.user)
        session1.end_session()
        
        session2 = StudySession.objects.create(user=self.user)
        # session2 is still active
        
        url = '/api/flashcards/sessions/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sessions', response.data)
        self.assertIn('total_sessions', response.data)
        self.assertEqual(response.data['total_sessions'], 2)
        self.assertEqual(len(response.data['sessions']), 2)

    def test_list_sessions_includes_statistics(self):
        """Test that session list includes statistics."""
        session = StudySession.objects.create(user=self.user)
        
        # Create card and reviews
        card = Card.objects.create(front='test', back='answer', user=self.user)
        CardReview.objects.create(
            card=card,
            session=session,
            user_score=0.9,
            interval_at_review=0,
            ease_factor_at_review=2.5
        )
        CardReview.objects.create(
            card=card,
            session=session,
            user_score=0.8,
            interval_at_review=1,
            ease_factor_at_review=2.5
        )
        
        session.end_session()
        
        url = '/api/flashcards/sessions/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session_data = response.data['sessions'][0]
        
        self.assertIn('cards_reviewed', session_data)
        self.assertIn('average_score', session_data)
        self.assertIn('active_minutes', session_data)
        self.assertEqual(session_data['cards_reviewed'], 2)
        self.assertAlmostEqual(session_data['average_score'], 0.85, places=2)

    def test_list_sessions_user_isolation(self):
        """Test that users only see their own sessions."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        StudySession.objects.create(user=self.user)
        StudySession.objects.create(user=other_user)
        
        url = '/api/flashcards/sessions/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_sessions'], 1)

    def test_session_with_card_reviews(self):
        """Test that sessions correctly track card reviews."""
        session = StudySession.objects.create(user=self.user)
        
        # Create cards and reviews
        card1 = Card.objects.create(front='card1', back='answer1', user=self.user)
        card2 = Card.objects.create(front='card2', back='answer2', user=self.user)
        
        CardReview.objects.create(
            card=card1,
            session=session,
            user_score=0.9,
            interval_at_review=0,
            ease_factor_at_review=2.5
        )
        CardReview.objects.create(
            card=card2,
            session=session,
            user_score=0.7,
            interval_at_review=1,
            ease_factor_at_review=2.5
        )
        
        # Verify session tracks reviews
        self.assertEqual(session.card_reviews.count(), 2)
        
        # End session and check statistics
        session.end_session()
        
        url = '/api/flashcards/sessions/'
        response = self.client.get(url)
        
        session_data = response.data['sessions'][0]
        self.assertEqual(session_data['cards_reviewed'], 2)
        self.assertAlmostEqual(session_data['average_score'], 0.8, places=2)

    def test_session_active_minutes_calculation(self):
        """Test that active minutes are calculated correctly in API."""
        session = StudySession.objects.create(user=self.user)
        start_time = session.start_time
        
        # Create activities
        SessionActivity.objects.create(
            session=session,
            timestamp=start_time + timedelta(seconds=30)
        )
        SessionActivity.objects.create(
            session=session,
            timestamp=start_time + timedelta(seconds=60)
        )
        
        session.end_time = start_time + timedelta(seconds=90)
        session.is_active = False
        session.save()
        
        url = '/api/flashcards/sessions/'
        response = self.client.get(url)
        
        session_data = response.data['sessions'][0]
        self.assertIn('active_minutes', session_data)
        self.assertIn('active_seconds', session_data)
        # Should be approximately 1.5 minutes (90 seconds)
        self.assertAlmostEqual(session_data['active_minutes'], 1.5, delta=0.1)
        self.assertEqual(session_data['active_seconds'], 90)
