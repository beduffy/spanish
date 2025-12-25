from django.test import TestCase
import os
from io import StringIO, BytesIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model
from flashcards.models import Sentence, Review, Card, CardReview, LEARNING_STEPS_DAYS, GRADUATING_INTERVAL_DAYS, LAPSE_INTERVAL_DAYS, MIN_EASE_FACTOR
from datetime import timedelta, date, datetime
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()

# Create your tests here.

class ImportCSVCommandTest(TestCase):
    def setUp(self):
        # Ensure the data directory exists for creating a temporary CSV if needed
        # For this test, we'll use StringIO, but good practice for other tests
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data') # Assuming tests.py is in flashcards/
        os.makedirs(self.data_dir, exist_ok=True)
        self.temp_csv_path = os.path.join(self.data_dir, 'test_import.csv')

    def tearDown(self):
        # Clean up the temporary CSV file if it was created
        if os.path.exists(self.temp_csv_path):
            os.remove(self.temp_csv_path)
        # Clean up Sentence objects created during tests
        Sentence.objects.all().delete()

    def _create_temp_csv(self, content):
        with open(self.temp_csv_path, 'w', newline='', encoding='utf-8') as f:
            f.write(content)
        return self.temp_csv_path

    def test_import_csv_success(self):
        csv_content = (
            "Number,Spanish Word,English Translation,Spanish Example,English Example,Comment,Chat GPTs explanation,Gemini explanation\n"
            "1,De,From,Él es de la ciudad de Nueva York.,He is from New York City.,Old base comment,GPT expl 1,Gemini expl 1\n"
            "2,Que,That,Esa es la chica que me gusta.,That is the girl that I like.,Another comment,,\n"
            "3,No,No/Don't,No hagas eso.,Don't do that.,,,,,"
        )
        temp_csv_file = self._create_temp_csv(csv_content)

        call_command('import_csv', temp_csv_file)

        self.assertEqual(Sentence.objects.count(), 6) # 3 rows * 2 directions

        s1_s2e = Sentence.objects.get(csv_number=1, translation_direction='S2E')
        self.assertEqual(s1_s2e.key_spanish_word, 'De')
        self.assertEqual(s1_s2e.key_word_english_translation, 'From')
        self.assertEqual(s1_s2e.spanish_sentence_example, 'Él es de la ciudad de Nueva York.')
        self.assertEqual(s1_s2e.english_sentence_example, 'He is from New York City.')
        self.assertEqual(s1_s2e.base_comment, 'Old base comment')
        self.assertEqual(s1_s2e.ai_explanation, "ChatGPT: GPT expl 1\nGemini: Gemini expl 1")

        s1_e2s = Sentence.objects.get(csv_number=1, translation_direction='E2S')
        self.assertEqual(s1_e2s.key_spanish_word, 'From') # English key word
        self.assertEqual(s1_e2s.key_word_english_translation, 'De') # Spanish translation
        self.assertEqual(s1_e2s.spanish_sentence_example, 'He is from New York City.') # English prompt
        self.assertEqual(s1_e2s.english_sentence_example, 'Él es de la ciudad de Nueva York.') # Spanish answer
        self.assertEqual(s1_e2s.base_comment, 'Old base comment')
        self.assertEqual(s1_e2s.ai_explanation, "ChatGPT: GPT expl 1\nGemini: Gemini expl 1")

        # Verify one field for S2E from another row to be sure
        s2_s2e = Sentence.objects.get(csv_number=2, translation_direction='S2E')
        self.assertEqual(s2_s2e.key_spanish_word, 'Que')
        self.assertIsNone(s2_s2e.ai_explanation)
        
        s3_e2s = Sentence.objects.get(csv_number=3, translation_direction='E2S')
        self.assertEqual(s3_e2s.base_comment, '')
        self.assertIsNone(s3_e2s.ai_explanation)


    def test_import_csv_duplicates_skipped(self):
        # First import
        csv_content_initial = (
            "Number,Spanish Word,English Translation,Spanish Example,English Example\n"
            "10,Hola,Hello,Hola Mundo,Hello World\n"
        )
        temp_csv_file_initial = self._create_temp_csv(csv_content_initial)
        call_command('import_csv', temp_csv_file_initial)
        self.assertEqual(Sentence.objects.count(), 2) # 1 row * 2 directions

        # Second import with a duplicate and a new entry
        csv_content_second = (
            "Number,Spanish Word,English Translation,Spanish Example,English Example\n"
            "10,Hola,Hello,Hola Mundo,Hello World\n"  # Duplicate
            "11,Adiós,Goodbye,Adiós Mundo,Goodbye World\n" # New
        )
        # Overwrite the temp CSV or create a new one for clarity if preferred
        temp_csv_file_second = self._create_temp_csv(csv_content_second) 
        
        # Use StringIO to capture stdout
        out = StringIO()
        call_command('import_csv', temp_csv_file_second, stdout=out)
        
        self.assertEqual(Sentence.objects.count(), 4) # 1 original row (2 cards) + 1 new row (2 cards)
        self.assertTrue(Sentence.objects.filter(csv_number=10, translation_direction='S2E').exists())
        self.assertTrue(Sentence.objects.filter(csv_number=10, translation_direction='E2S').exists())
        self.assertTrue(Sentence.objects.filter(csv_number=11, translation_direction='S2E').exists())
        self.assertTrue(Sentence.objects.filter(csv_number=11, translation_direction='E2S').exists())
        
        output = out.getvalue()
        self.assertIn("Skipping already imported S2E sentence with CSV Number: 10", output)
        self.assertIn("Skipping already imported E2S sentence with CSV Number: 10", output)
        self.assertIn("Successfully imported 1 new S2E sentences and 1 new E2S sentences.", output)
        self.assertIn("Skipped 1 S2E and 1 E2S already existing sentences.", output)


    def test_import_csv_missing_required_column(self):
        csv_content = (
            "Number,Spanish Word,English Translation,Spanish Example\n" # Missing 'English Example'
            "20,Test,Test,Test Spanish Sent,,,,\n"
        )
        temp_csv_file = self._create_temp_csv(csv_content)
        
        with self.assertRaisesRegex(CommandError, "Missing required columns in CSV: English Example"):
            call_command('import_csv', temp_csv_file)

    def test_import_csv_malformed_number(self):
        csv_content = (
            "Number,Spanish Word,English Translation,Spanish Example,English Example\n"
            "ABC,Mal,Bad,Sentence Mal,Bad Sentence\n" # Number is not an int
        )
        temp_csv_file = self._create_temp_csv(csv_content)
        out_err = StringIO() # Capture stderr for error messages from the command
        call_command('import_csv', temp_csv_file, stderr=out_err)
        # Check that no sentence was created
        self.assertEqual(Sentence.objects.count(), 0)
        # Check for specific error message
        self.assertIn("Error processing row 2: invalid literal for int() with base 10: 'ABC'", out_err.getvalue())

    def test_import_csv_empty_file(self):
        csv_content = ("Number,Spanish Word,English Translation,Spanish Example,English Example\n") # Only header
        temp_csv_file = self._create_temp_csv(csv_content)
        out = StringIO()
        call_command('import_csv', temp_csv_file, stdout=out)
        self.assertEqual(Sentence.objects.count(), 0)
        self.assertIn("Successfully imported 0 new S2E sentences and 0 new E2S sentences.", out.getvalue())

class SRSLogicTests(TestCase):
    def _create_sentence(self, csv_number=100, key_spanish_word="Test Word", 
                           translation_direction='S2E', # Added parameter
                           ease_factor=2.5, interval_days=0, 
                           is_learning=True, consecutive_correct_reviews=0,
                           next_review_date=None, total_reviews=0, total_score_sum=0.0):
        if next_review_date is None:
            next_review_date = timezone.now().date()
        
        # Delete if exists to ensure clean slate for specific csv_number and direction in tests
        Sentence.objects.filter(csv_number=csv_number, translation_direction=translation_direction).delete()
        
        # Adjust prompt/answer for E2S if needed for specific test setups, 
        # though import_csv handles the primary swap.
        # For basic _create_sentence, we'll keep it simple unless a test needs explicit swapping here.
        s_example = "Test Spanish Example"
        e_example = "Test English Example"
        kw_s = key_spanish_word
        kw_e = "Test Translation"

        if translation_direction == 'E2S':
            s_example, e_example = e_example, s_example
            kw_s, kw_e = kw_e, kw_s # kw_s field stores the prompt key, kw_e the answer key

        return Sentence.objects.create(
            csv_number=csv_number,
            translation_direction=translation_direction, # Use the parameter
            key_spanish_word=kw_s,
            key_word_english_translation=kw_e,
            spanish_sentence_example=s_example,
            english_sentence_example=e_example,
            ease_factor=ease_factor,
            interval_days=interval_days,
            is_learning=is_learning,
            consecutive_correct_reviews=consecutive_correct_reviews,
            next_review_date=next_review_date,
            total_reviews=total_reviews,
            total_score_sum=total_score_sum
        )

    def test_new_card_perfect_score(self):
        sentence = self._create_sentence(interval_days=0, is_learning=True, consecutive_correct_reviews=0)
        original_ef = sentence.ease_factor
        
        sentence.process_review(user_score=0.95, review_comment="Perfect!") 

        self.assertEqual(sentence.interval_days, 1, "Interval should be 1 day after first learning pass")
        self.assertAlmostEqual(sentence.ease_factor, original_ef + 0.1, delta=0.01, msg="EF should increase for perfect score")
        self.assertTrue(sentence.is_learning, "Should still be in learning phase")
        self.assertEqual(sentence.consecutive_correct_reviews, 1)
        self.assertEqual(sentence.next_review_date, timezone.now().date() + timedelta(days=1))
        self.assertEqual(sentence.total_reviews, 1)
        self.assertEqual(sentence.total_score_sum, 0.95)
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertEqual(review.sentence, sentence)
        self.assertEqual(review.user_score, 0.95)
        self.assertEqual(review.user_comment_addon, "Perfect!")
        self.assertEqual(review.interval_at_review, 0) # Interval before this review
        self.assertEqual(review.ease_factor_at_review, original_ef) # EF before this review

    def test_new_card_medium_score(self):
        sentence = self._create_sentence(interval_days=0, is_learning=True, consecutive_correct_reviews=0)
        original_ef = sentence.ease_factor # Should be 2.5
        # user_score = 0.7 (q=3)
        # EF_new = EF + (0.1 - (5-3)*(0.08+(5-3)*0.02)) = EF + (0.1 - 2*(0.08+0.04)) = EF + (0.1 - 2*0.12) = EF + (0.1 - 0.24) = EF - 0.14
        expected_ef = original_ef - 0.14 

        sentence.process_review(user_score=0.7, review_comment="Okay")

        self.assertEqual(sentence.interval_days, 1, "Interval should be 1 day after first learning pass")
        self.assertAlmostEqual(sentence.ease_factor, expected_ef, delta=0.01, msg="EF should decrease for q=3 score")
        self.assertTrue(sentence.is_learning)
        self.assertEqual(sentence.consecutive_correct_reviews, 0)
        self.assertEqual(sentence.next_review_date, timezone.now().date() + timedelta(days=1))
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.first().user_score, 0.7)

    def test_new_card_fail_score(self):
        sentence = self._create_sentence(interval_days=0, is_learning=True, consecutive_correct_reviews=0)
        original_ef = sentence.ease_factor
        
        sentence.process_review(user_score=0.3) # q=1 (fail)

        self.assertEqual(sentence.interval_days, 0, "Interval should reset to 0 (or first step) on fail")
        self.assertAlmostEqual(sentence.ease_factor, original_ef, delta=0.01, msg="EF should ideally not change much or slightly decrease on first fail") # Or define penalty
        self.assertTrue(sentence.is_learning)
        self.assertEqual(sentence.consecutive_correct_reviews, 0)
        self.assertEqual(sentence.next_review_date, timezone.now().date() + timedelta(days=0)) # Or 1 if first step is 1 day
        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.first().user_score, 0.3)

    def test_learning_step1_pass_perfect(self):
        # Card has passed initial review (interval_days=0), now at interval_days=1 (LEARNING_STEPS_DAYS[0])
        sentence = self._create_sentence(interval_days=LEARNING_STEPS_DAYS[0], is_learning=True, consecutive_correct_reviews=1, ease_factor=2.6)
        original_ef = sentence.ease_factor # Should be 2.6 from previous perfect review
        
        sentence.process_review(user_score=0.95) # Perfect score again (q=5)
        # Expected EF: 2.6 + 0.1 = 2.7

        self.assertEqual(sentence.interval_days, LEARNING_STEPS_DAYS[1], "Interval should advance to the second learning step (3 days)")
        self.assertAlmostEqual(sentence.ease_factor, original_ef + 0.1, delta=0.01)
        self.assertTrue(sentence.is_learning, "Should still be in learning phase")
        self.assertEqual(sentence.consecutive_correct_reviews, 2)
        self.assertEqual(sentence.next_review_date, timezone.now().date() + timedelta(days=LEARNING_STEPS_DAYS[1]))
        self.assertEqual(Review.objects.filter(sentence=sentence).count(), 1) # Check a new review was created

    def test_learning_step1_fail(self):
        sentence = self._create_sentence(interval_days=LEARNING_STEPS_DAYS[0], is_learning=True, consecutive_correct_reviews=1, ease_factor=2.6)
        original_ef = sentence.ease_factor

        sentence.process_review(user_score=0.3) # Fail (q=1)

        self.assertEqual(sentence.interval_days, 0, "Interval should reset to 0 on failing a learning step")
        self.assertAlmostEqual(sentence.ease_factor, original_ef, delta=0.01, msg="EF should not change on learning step fail, or only slightly penalized if desired")
        self.assertTrue(sentence.is_learning)
        self.assertEqual(sentence.consecutive_correct_reviews, 0, "Consecutive good scores should reset on fail")
        self.assertEqual(sentence.next_review_date, timezone.now().date() + timedelta(days=0))

    def test_graduation_pass_perfect(self):
        # Card is at the last learning step (interval_days = LEARNING_STEPS_DAYS[1] = 3 days)
        sentence = self._create_sentence(interval_days=LEARNING_STEPS_DAYS[1], is_learning=True, consecutive_correct_reviews=2, ease_factor=2.7)
        original_ef = sentence.ease_factor # Should be 2.7
        # Expected EF: 2.7 + 0.1 = 2.8

        sentence.process_review(user_score=0.95) # Perfect score (q=5)

        self.assertEqual(sentence.interval_days, GRADUATING_INTERVAL_DAYS, f"Interval should be graduating interval {GRADUATING_INTERVAL_DAYS} days")
        self.assertAlmostEqual(sentence.ease_factor, original_ef + 0.1, delta=0.01)
        self.assertFalse(sentence.is_learning, "Card should have graduated")
        self.assertEqual(sentence.consecutive_correct_reviews, 3)
        self.assertEqual(sentence.next_review_date, timezone.now().date() + timedelta(days=GRADUATING_INTERVAL_DAYS))

    def test_graduation_fail(self):
        # Card is at the last learning step (interval_days = LEARNING_STEPS_DAYS[1] = 3 days)
        sentence = self._create_sentence(interval_days=LEARNING_STEPS_DAYS[1], is_learning=True, consecutive_correct_reviews=2, ease_factor=2.7)
        original_ef = sentence.ease_factor

        sentence.process_review(user_score=0.3) # Fail (q=1)

        self.assertEqual(sentence.interval_days, 0, "Interval should reset to 0 on failing last learning step before graduation")
        self.assertAlmostEqual(sentence.ease_factor, original_ef, delta=0.01)
        self.assertTrue(sentence.is_learning, "Card should remain in learning")
        self.assertEqual(sentence.consecutive_correct_reviews, 0)
        self.assertEqual(sentence.next_review_date, timezone.now().date() + timedelta(days=0))

    def test_graduated_card_review_perfect(self):
        initial_interval = 10
        initial_ef = 2.5
        sentence = self._create_sentence(interval_days=initial_interval, is_learning=False, ease_factor=initial_ef, consecutive_correct_reviews=3)
        
        # Expected new interval = round(10 * 2.5) = 25
        # Expected new EF = 2.5 + 0.1 = 2.6
        sentence.process_review(user_score=0.95) # Perfect (q=5)

        self.assertEqual(sentence.interval_days, round(initial_interval * initial_ef))
        self.assertFalse(sentence.is_learning)
        self.assertAlmostEqual(sentence.ease_factor, initial_ef + 0.1, delta=0.01)
        self.assertEqual(sentence.consecutive_correct_reviews, 4)
        self.assertEqual(sentence.next_review_date, timezone.now().date() + timedelta(days=round(initial_interval * initial_ef)))

    def test_graduated_card_review_medium(self):
        initial_interval = 10
        initial_ef = 2.5
        sentence = self._create_sentence(interval_days=initial_interval, is_learning=False, ease_factor=initial_ef, consecutive_correct_reviews=3)
        
        # score = 0.7 (q=3), EF = 2.5 - 0.14 = 2.36
        # Expected new interval = round(10 * 2.36) = 24 (using NEW EF for interval calculation is a common SM2 variant)
        # Let's assume for now interval is calculated with OLD EF, then EF is updated.
        # Anki actually does: new_interval = old_interval * old_ef (if good), then updates EF for next time.
        # Let's test with old_ef for interval calculation for now, as per current model logic. So, round(10 * 2.5) = 25
        # The model updates EF *after* interval calculation for graduated cards if q>=3.

        sentence.process_review(user_score=0.7) # Medium (q=3)

        self.assertEqual(sentence.interval_days, round(initial_interval * initial_ef), "Interval should be calculated with EF before its update for this review")
        self.assertFalse(sentence.is_learning)
        self.assertAlmostEqual(sentence.ease_factor, initial_ef - 0.14, delta=0.01, msg="EF should decrease for q=3 on review card")
        self.assertEqual(sentence.consecutive_correct_reviews, 0, "Consecutive should reset as score is not > 0.8")

    def test_graduated_card_lapse(self):
        initial_interval = 20
        initial_ef = 2.5
        sentence = self._create_sentence(interval_days=initial_interval, is_learning=False, ease_factor=initial_ef, consecutive_correct_reviews=5)
        expected_ef_after_lapse = max(MIN_EASE_FACTOR, initial_ef - 0.20)

        sentence.process_review(user_score=0.1) # Fail (q=0)

        self.assertTrue(sentence.is_learning, "Card should re-enter learning phase on lapse")
        self.assertEqual(sentence.interval_days, LAPSE_INTERVAL_DAYS, f"Interval should reset to {LAPSE_INTERVAL_DAYS} on lapse")
        self.assertAlmostEqual(sentence.ease_factor, expected_ef_after_lapse, delta=0.01, msg="EF should be penalized on lapse")
        self.assertEqual(sentence.consecutive_correct_reviews, 0, "Consecutive should reset on lapse")
        self.assertEqual(sentence.next_review_date, timezone.now().date() + timedelta(days=LAPSE_INTERVAL_DAYS))

    def test_ease_factor_min_boundary(self):
        # Test EF doesn't go below MIN_EASE_FACTOR
        # Start with EF already at min
        sentence = self._create_sentence(is_learning=False, interval_days=10, ease_factor=MIN_EASE_FACTOR)
        sentence.process_review(user_score=0.7) # q=3, which would normally decrease EF
        self.assertAlmostEqual(sentence.ease_factor, MIN_EASE_FACTOR, delta=0.01, msg=f"EF should not go below {MIN_EASE_FACTOR}")

        # Test EF reduction stopping at MIN_EASE_FACTOR
        sentence2 = self._create_sentence(csv_number=101, is_learning=False, interval_days=10, ease_factor=MIN_EASE_FACTOR + 0.05)
        sentence2.process_review(user_score=0.7) # q=3, EF formula would be (MIN_EASE_FACTOR + 0.05) - 0.14
        self.assertAlmostEqual(sentence2.ease_factor, MIN_EASE_FACTOR, delta=0.01, msg=f"EF should be capped at {MIN_EASE_FACTOR}")

        # Test EF reduction on lapse stopping at MIN_EASE_FACTOR
        sentence3 = self._create_sentence(csv_number=102, is_learning=False, interval_days=10, ease_factor=MIN_EASE_FACTOR + 0.1)
        sentence3.process_review(user_score=0.1) # Lapse, EF penalty is -0.20
        self.assertAlmostEqual(sentence3.ease_factor, MIN_EASE_FACTOR, delta=0.01, msg=f"EF penalty on lapse should be capped at {MIN_EASE_FACTOR}")

    # More tests might be needed for edge cases with interval rounding, very high EFs, etc.

class NextCardAPITests(APITestCase):
    # Helper method from SRSLogicTests, slightly adapted
    def _create_sentence(self, csv_number=100, key_spanish_word="Test Word", 
                           translation_direction='S2E', # Added parameter
                           ease_factor=2.5, interval_days=0, 
                           is_learning=True, consecutive_correct_reviews=0,
                           next_review_date=None, total_reviews=0, total_score_sum=0.0,
                           spanish_sentence_example="Test Spanish Example API", 
                           english_sentence_example="Test English Example API",
                           key_word_english_translation="Test Translation API",
                           base_comment="Base comment API",
                           ai_explanation="AI Explanation API",
                           user=None):
        if next_review_date is None:
            next_review_date = timezone.now().date()
        
        Sentence.objects.filter(csv_number=csv_number, translation_direction=translation_direction).delete()
        
        # Simplified field assignment; specific E2S content swapping can be done in test if needed
        # or by how key_spanish_word, spanish_sentence_example etc. are passed for E2S calls.
        # For E2S, the caller should pass the English content to spanish_sentence_example, etc.
        return Sentence.objects.create(
            csv_number=csv_number,
            translation_direction=translation_direction,
            key_spanish_word=key_spanish_word,
            key_word_english_translation=key_word_english_translation,
            spanish_sentence_example=spanish_sentence_example,
            english_sentence_example=english_sentence_example,
            base_comment=base_comment,
            ai_explanation=ai_explanation,
            ease_factor=ease_factor,
            interval_days=interval_days,
            is_learning=is_learning,
            consecutive_correct_reviews=consecutive_correct_reviews,
            next_review_date=next_review_date,
            total_reviews=total_reviews,
            total_score_sum=total_score_sum,
            user=user or self.test_user
        )

    def setUp(self):
        # Create test user and authenticate
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.test_user)
        
        # Clean up Sentence objects before each test
        Sentence.objects.all().delete()
        Review.objects.all().delete() # Also clean reviews if they might interfere

    def test_get_next_card_review_card_due(self):
        """
        Tests that if a review card is due, it is returned.
        """
        today = timezone.now().date()
        review_sentence = self._create_sentence(
            csv_number=201, 
            next_review_date=today - timedelta(days=1), 
            is_learning=False, 
            interval_days=10
        )
        # A new card that shouldn\'t be picked if a review is due
        self._create_sentence(csv_number=202, next_review_date=today, interval_days=0, is_learning=True)
        # A review card not yet due
        self._create_sentence(csv_number=203, next_review_date=today + timedelta(days=1), is_learning=False)

        response = self.client.get("/api/flashcards/next-card/") # URL placeholder
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['csv_number'], review_sentence.csv_number)
        self.assertEqual(response.data['key_spanish_word'], review_sentence.key_spanish_word)

    def test_get_next_card_new_card_available(self):
        """
        Tests that if no review cards are due, a new card is returned.
        """
        today = timezone.now().date()
        # A review card not yet due
        self._create_sentence(csv_number=301, next_review_date=today + timedelta(days=5), is_learning=False)
        new_sentence = self._create_sentence(
            csv_number=302, 
            next_review_date=today, # New cards have next_review_date as today
            interval_days=0, # New cards have interval_days = 0
            is_learning=True 
        )
        # Another new card with higher csv_number, to ensure ordering by csv_number for new cards
        self._create_sentence(csv_number=303, next_review_date=today, interval_days=0, is_learning=True)

        response = self.client.get("/api/flashcards/next-card/") # URL placeholder
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['csv_number'], new_sentence.csv_number) # Expecting the one with lower csv_number
        self.assertTrue(response.data['is_learning'])

    def test_get_next_card_no_cards_available(self):
        """
        Tests that if no review cards are due and no new cards are available,
        a 204 No Content or an appropriate message is returned.
        """
        today = timezone.now().date()
        # A review card not yet due
        self._create_sentence(csv_number=401, next_review_date=today + timedelta(days=5), is_learning=False)
        # A new card that has already been "processed" somehow and has a future next_review_date
        # (e.g. if user set max new cards to 0 for the day, and it was moved to tomorrow)
        # For now, let\'s assume new cards only appear if next_review_date is today and interval is 0.
        # So, simply not creating any "available" new cards.

        response = self.client.get("/api/flashcards/next-card/") # URL placeholder
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT) # Or HTTP_404_NOT_FOUND if preferred

    def test_get_next_card_prioritizes_older_review_card(self):
        """
        Tests that if multiple review cards are due, the one with the older 
        next_review_date is returned. If dates are same, older csv_number (implicit by creation order usually).
        """
        today = timezone.now().date()
        older_review_sentence = self._create_sentence(
            csv_number=501, 
            next_review_date=today - timedelta(days=2), # Due 2 days ago
            is_learning=False, 
            interval_days=10
        )
        newer_review_sentence = self._create_sentence(
            csv_number=502, 
            next_review_date=today - timedelta(days=1), # Due 1 day ago
            is_learning=False, 
            interval_days=10
        )
        self._create_sentence(csv_number=503, next_review_date=today, interval_days=0, is_learning=True) # New card

        response = self.client.get("/api/flashcards/next-card/") # URL placeholder
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['csv_number'], older_review_sentence.csv_number)

    def test_get_next_card_new_card_order_by_csv_number(self):
        """
        Tests that if multiple new cards are available, the one with the lower
        csv_number is returned.
        """
        today = timezone.now().date()
        new_sentence_later = self._create_sentence(
            csv_number=602, 
            next_review_date=today, 
            interval_days=0, 
            is_learning=True
        )
        new_sentence_earlier = self._create_sentence(
            csv_number=601, 
            next_review_date=today, 
            interval_days=0, 
            is_learning=True
        )

        response = self.client.get("/api/flashcards/next-card/") # URL placeholder
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['csv_number'], new_sentence_earlier.csv_number)
        self.assertTrue(response.data['is_learning'])

class SubmitReviewAPITests(APITestCase):
    def _create_sentence(self, csv_number=700, key_spanish_word="Submit Word", 
                           translation_direction='S2E', # Added parameter
                           ease_factor=2.5, interval_days=0, 
                           is_learning=True, consecutive_correct_reviews=0,
                           next_review_date=None, base_comment="Initial comment.",
                           total_reviews=0, total_score_sum=0.0,
                           user=None):
        if next_review_date is None:
            next_review_date = timezone.now().date()
        
        Sentence.objects.filter(csv_number=csv_number, translation_direction=translation_direction).delete()
        
        s_example = "Submit Spanish Example"
        e_example = "Submit English Example"
        kw_s = key_spanish_word
        kw_e = "Submit Translation"

        if translation_direction == 'E2S':
            s_example, e_example = e_example, s_example
            kw_s, kw_e = kw_e, kw_s

        return Sentence.objects.create(
            csv_number=csv_number,
            translation_direction=translation_direction,
            key_spanish_word=kw_s,
            key_word_english_translation=kw_e,
            spanish_sentence_example=s_example,
            english_sentence_example=e_example,
            base_comment=base_comment,
            ease_factor=ease_factor,
            interval_days=interval_days,
            is_learning=is_learning,
            consecutive_correct_reviews=consecutive_correct_reviews,
            next_review_date=next_review_date,
            total_reviews=total_reviews,
            total_score_sum=total_score_sum,
            user=user or self.test_user
        )

    def setUp(self):
        # Create test user and authenticate
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.test_user)
        
        Sentence.objects.all().delete()
        Review.objects.all().delete()
        self.submit_review_url = "/api/flashcards/submit-review/" # Will be added to urls.py

    def test_submit_review_success_new_card(self):
        """
        Tests successful review submission for a new card.
        Checks SRS updates, Review object creation, and base_comment update.
        """
        sentence = self._create_sentence(csv_number=701, interval_days=0, is_learning=True, base_comment="Original.")
        payload = {
            "sentence_id": sentence.sentence_id,
            "user_score": 0.95, # q=5 (perfect)
            "user_comment_addon": "Learned this one quickly!"
        }
        
        response = self.client.post(self.submit_review_url, payload, format='json') 
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        sentence.refresh_from_db()
        self.assertEqual(sentence.interval_days, LEARNING_STEPS_DAYS[0]) 
        self.assertTrue(sentence.is_learning)
        self.assertEqual(sentence.consecutive_correct_reviews, 1)
        self.assertEqual(sentence.next_review_date, timezone.now().date() + timedelta(days=LEARNING_STEPS_DAYS[0]))
        self.assertIn("Learned this one quickly!", sentence.base_comment)
        self.assertIn(timezone.now().strftime('%H:%M %b %d, %Y'), sentence.base_comment) # Check for timestamp format from view
        
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertEqual(review.sentence, sentence)
        self.assertEqual(review.user_score, 0.95)
        self.assertEqual(review.user_comment_addon, "Learned this one quickly!")

    def test_submit_review_comment_append(self):
        """
        Tests that new comments are correctly appended to existing base_comment.
        """
        initial_comment = "This is the first comment."
        sentence = self._create_sentence(csv_number=702, base_comment=initial_comment)
        
        first_review_comment = "My first note on this."
        payload1 = {"sentence_id": sentence.sentence_id, "user_score": 0.8, "user_comment_addon": first_review_comment}
        response1 = self.client.post(self.submit_review_url, payload1, format='json') 
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        sentence.refresh_from_db()
        self.assertIn(initial_comment, sentence.base_comment)
        self.assertIn(first_review_comment, sentence.base_comment)
        first_timestamp_check = timezone.now().strftime('%H:%M %b %d, %Y') # Approximate check
        self.assertIn(first_timestamp_check[:10], sentence.base_comment) # Check date part of timestamp at least

        # Simulate a bit of time passing for a new timestamp, though in tests it might be too fast
        # For robust check, one might mock timezone.now() in the view or check for two distinct timestamps
        
        second_review_comment = "Another thought."
        payload2 = {"sentence_id": sentence.sentence_id, "user_score": 0.7, "user_comment_addon": second_review_comment}
        response2 = self.client.post(self.submit_review_url, payload2, format='json')
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        sentence.refresh_from_db()
        
        self.assertTrue(sentence.base_comment.startswith(initial_comment))
        self.assertIn(first_review_comment, sentence.base_comment)
        self.assertIn(second_review_comment, sentence.base_comment)
        self.assertTrue(sentence.base_comment.count(":") >= 2) # Check for at least two timestamp colons

    def test_submit_review_invalid_score_too_high(self):
        """
        Tests that submitting a score > 1.0 results in a 400 Bad Request.
        """
        sentence = self._create_sentence(csv_number=703)
        payload = {"sentence_id": sentence.sentence_id, "user_score": 1.1, "user_comment_addon": "Too high"}
        response = self.client.post(self.submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user_score", response.data)
        self.assertIn("Ensure this value is less than or equal to 1.0.", str(response.data["user_score"])) # More specific check

    def test_submit_review_non_existent_sentence_id(self):
        """
        Tests that submitting a review for a non-existent sentence_id results in a 404 Not Found.
        """
        payload = {"sentence_id": 9999, "user_score": 0.5, "user_comment_addon": "Doesn't exist"}
        response = self.client.post(self.submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Sentence not found.")

    def test_submit_review_success_learning_card(self):
        """Tests review submission for a card in a learning step, advancing it."""
        sentence = self._create_sentence(
            csv_number=704, 
            is_learning=True, 
            interval_days=LEARNING_STEPS_DAYS[0], # e.g., 1 day
            consecutive_correct_reviews=1,
            base_comment="Learning this."
        )
        original_ef = sentence.ease_factor
        payload = {
            "sentence_id": sentence.sentence_id,
            "user_score": 0.9, # Good score
            "user_comment_addon": "Still learning, but better!"
        }
        response = self.client.post(self.submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sentence.refresh_from_db()
        self.assertEqual(sentence.interval_days, LEARNING_STEPS_DAYS[1]) # Advance to next step
        self.assertTrue(sentence.is_learning)
        self.assertEqual(sentence.consecutive_correct_reviews, 2)
        self.assertIn("Still learning, but better!", sentence.base_comment)

    def test_submit_review_success_graduated_card(self):
        """Tests review submission for a graduated card, calculating new interval."""
        initial_interval = GRADUATING_INTERVAL_DAYS # e.g., 7 days
        sentence = self._create_sentence(
            csv_number=705, 
            is_learning=False, 
            interval_days=initial_interval,
            ease_factor=2.5,
            consecutive_correct_reviews=3 # Already graduated implies some correct reviews
        )
        payload = {
            "sentence_id": sentence.sentence_id,
            "user_score": 0.85, # Good score
            "user_comment_addon": "Reviewed well."
        }
        response = self.client.post(self.submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sentence.refresh_from_db()
        expected_new_interval = round(initial_interval * sentence.ease_factor) # EF might have slightly changed
        self.assertEqual(sentence.interval_days, expected_new_interval)
        self.assertFalse(sentence.is_learning)
        self.assertIn("Reviewed well.", sentence.base_comment)

    def test_submit_review_lapse_card(self):
        """Tests review submission for a graduated card that lapses (low score)."""
        sentence = self._create_sentence(
            csv_number=706,
            is_learning=False,
            interval_days=20, # Graduated
            ease_factor=2.3
        )
        original_base_comment = sentence.base_comment
        payload = {
            "sentence_id": sentence.sentence_id,
            "user_score": 0.2, # Fail score
            "user_comment_addon": "Forgot this one completely!"
        }
        response = self.client.post(self.submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sentence.refresh_from_db()
        self.assertTrue(sentence.is_learning, "Card should re-enter learning on lapse.")
        self.assertEqual(sentence.interval_days, LAPSE_INTERVAL_DAYS)
        self.assertEqual(sentence.consecutive_correct_reviews, 0)
        self.assertIn("Forgot this one completely!", sentence.base_comment)
        self.assertTrue(len(sentence.base_comment) > len(original_base_comment))

    def test_submit_review_no_comment(self):
        """Tests review submission with no comment addon."""
        sentence = self._create_sentence(csv_number=707, base_comment="Only initial comment.")
        original_base_comment = sentence.base_comment
        payload = {
            "sentence_id": sentence.sentence_id,
            "user_score": 0.9,
            "user_comment_addon": "" # Empty comment
        }
        response = self.client.post(self.submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sentence.refresh_from_db()
        self.assertEqual(sentence.base_comment, original_base_comment, "Base comment should not change if addon is empty.")
        self.assertTrue(sentence.interval_days > 0) # Check SRS logic still ran

    def test_submit_review_null_comment(self):
        """Tests review submission with null comment addon."""
        sentence = self._create_sentence(csv_number=708, base_comment="Base comment here.")
        original_base_comment = sentence.base_comment
        payload = {
            "sentence_id": sentence.sentence_id,
            "user_score": 0.7,
            "user_comment_addon": None # Null comment
        }
        response = self.client.post(self.submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sentence.refresh_from_db()
        self.assertEqual(sentence.base_comment, original_base_comment, "Base comment should not change if addon is null.")

    def test_submit_review_invalid_score_too_low(self):
        """Tests submitting a score < 0.0 results in a 400 Bad Request."""
        sentence = self._create_sentence(csv_number=709)
        payload = {"sentence_id": sentence.sentence_id, "user_score": -0.1}
        response = self.client.post(self.submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user_score", response.data)
        self.assertIn("Ensure this value is greater than or equal to 0.0.", str(response.data["user_score"])) 

    def test_submit_review_missing_score(self):
        """Tests submitting without a score results in a 400 Bad Request."""
        sentence = self._create_sentence(csv_number=710)
        payload = {"sentence_id": sentence.sentence_id, "user_comment_addon": "No score given."}
        response = self.client.post(self.submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user_score", response.data)
        self.assertIn("This field is required.", str(response.data["user_score"])) 

    def test_submit_review_missing_sentence_id(self):
        """Tests submitting without a sentence_id results in a 400 Bad Request."""
        payload = {"user_score": 0.5, "user_comment_addon": "No sentence_id."}
        response = self.client.post(self.submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sentence_id", response.data)
        self.assertIn("This field is required.", str(response.data["sentence_id"])) 

    # TODO: Consider edge case for timestamp generation if tests run too fast for different timestamps in append test.
    # Might need to mock timezone.now() for more precise timestamp append tests if it becomes an issue.

class StatisticsAPITests(APITestCase):
    def setUp(self):
        # Create test user and authenticate
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.test_user)
        
        Sentence.objects.all().delete()
        Review.objects.all().delete()
        self.stats_url = "/api/flashcards/statistics/" # To be added to urls.py
        self.today = timezone.now().date()
        self.one_day_ago = self.today - timedelta(days=1)
        self.three_days_ago = self.today - timedelta(days=3)
        self.eight_days_ago = self.today - timedelta(days=8)

    def _create_sentence_for_stats(self, csv_number, translation_direction='S2E', # Added parameter
                                   is_learning=False, interval_days=30, 
                                   consecutive_correct_reviews=3, total_reviews=5, total_score_sum=4.0, ease_factor=2.5,
                                   user=None):
        
        Sentence.objects.filter(csv_number=csv_number, translation_direction=translation_direction).delete()
        
        key_s = f"Word {csv_number}"
        key_e = f"Translation {csv_number}"
        spanish_ex = f"Spanish Ex {csv_number}"
        english_ex = f"English Ex {csv_number}"

        if translation_direction == 'E2S':
            key_s, key_e = key_e, key_s
            spanish_ex, english_ex = english_ex, spanish_ex

        return Sentence.objects.create(
            csv_number=csv_number,
            translation_direction=translation_direction,
            key_spanish_word=key_s,
            key_word_english_translation=key_e,
            spanish_sentence_example=spanish_ex,
            english_sentence_example=english_ex,
            is_learning=is_learning,
            interval_days=interval_days,
            consecutive_correct_reviews=consecutive_correct_reviews,
            next_review_date=self.today + timedelta(days=interval_days),
            total_reviews=total_reviews,
            total_score_sum=total_score_sum,
            ease_factor=ease_factor,
            user=user or self.test_user
        )

    def _create_review(self, sentence, score, timestamp_obj, interval_at_review=0):
        # Ensure timestamp_obj is datetime and aware
        if isinstance(timestamp_obj, date) and not isinstance(timestamp_obj, datetime):
            aware_timestamp = timezone.make_aware(datetime.combine(timestamp_obj, datetime.min.time()))
        elif isinstance(timestamp_obj, datetime) and timezone.is_naive(timestamp_obj):
            aware_timestamp = timezone.make_aware(timestamp_obj)
        else:
            aware_timestamp = timestamp_obj # Assuming it's already an aware datetime

        return Review.objects.create(
            sentence=sentence,
            user_score=score,
            review_timestamp=aware_timestamp,
            interval_at_review=interval_at_review, 
            ease_factor_at_review=sentence.ease_factor 
        )

    def test_get_statistics_no_data(self):
        """Test statistics endpoint when there is no data."""
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_stats = {
            "reviews_today": 0,
            "new_cards_reviewed_today": 0,
            "reviews_this_week": 0,
            "total_reviews_all_time": 0,
            "overall_average_score": None,
            "total_sentences": 0,
            "sentences_mastered": 0,
            "sentences_learned": 0,
            "percentage_learned": None
        }
        self.assertEqual(response.data, expected_stats)

    def test_get_statistics_with_basic_data(self):
        """Test statistics with some reviews and sentences."""
        # s1: Learned, but not mastered
        s1 = self._create_sentence_for_stats(
            csv_number=801, 
            is_learning=True, # Clearly not mastered
            interval_days=1, 
            consecutive_correct_reviews=1, 
            total_reviews=1, 
            total_score_sum=0.9, 
            ease_factor=2.5
        )
        # s2: Learned, but not mastered
        s2 = self._create_sentence_for_stats(
            csv_number=802, 
            is_learning=True, # Clearly not mastered
            interval_days=3, 
            consecutive_correct_reviews=2, 
            total_reviews=2, 
            total_score_sum=1.5, # avg 0.75
            ease_factor=2.6
        )
        # s3: New, not reviewed, not learned
        s3 = self._create_sentence_for_stats(
            csv_number=803, 
            is_learning=True, 
            interval_days=0, 
            consecutive_correct_reviews=0, 
            total_reviews=0, 
            total_score_sum=0.0,
            ease_factor=2.5
        ) 
        # s4_mastered: Clearly mastered
        s4_mastered = self._create_sentence_for_stats(
            csv_number=804, 
            is_learning=False, 
            interval_days=GRADUATING_INTERVAL_DAYS + 1, 
            consecutive_correct_reviews=3, 
            total_reviews=5, 
            total_score_sum=4.5, # avg 0.9
            ease_factor=2.8
        )

        # Reviews Today - make timestamps deterministic relative to self.today
        # Ensure these are distinct, aware datetime objects for 'today'
        review_time_today_1 = timezone.make_aware(datetime.combine(self.today, datetime.min.time())) + timedelta(hours=10)
        review_time_today_2 = timezone.make_aware(datetime.combine(self.today, datetime.min.time())) + timedelta(hours=12)

        self._create_review(s1, 0.9, review_time_today_1, interval_at_review=0) # New card review today
        self._create_review(s2, 0.8, review_time_today_2, interval_at_review=5) # Existing card review today
        
        # Reviews This Week (but not today)
        # Ensure these are also distinct, aware datetime objects for their respective days
        review_time_one_day_ago = timezone.make_aware(datetime.combine(self.one_day_ago, datetime.min.time())) + timedelta(hours=10)
        review_time_three_days_ago = timezone.make_aware(datetime.combine(self.three_days_ago, datetime.min.time())) + timedelta(hours=10)

        self._create_review(s1, 0.7, review_time_one_day_ago, interval_at_review=1)
        self._create_review(s2, 0.7, review_time_three_days_ago, interval_at_review=10)

        # Reviews Older than a week
        review_time_eight_days_ago = timezone.make_aware(datetime.combine(self.eight_days_ago, datetime.min.time())) + timedelta(hours=10)
        self._create_review(s4_mastered, 0.9, review_time_eight_days_ago, interval_at_review=20)

        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Expected calculations based on PRD and setup
        # total_sentences = 4 (s1, s2, s3, s4_mastered)
        # sentences_learned = 3 (s1, s2, s4_mastered, as s3 has 0 reviews)
        # percentage_learned = (3/4)*100 = 75.0
        # reviews_today = 2
        # new_cards_reviewed_today = 1 (s1's first review was today and interval_at_review=0)
        # reviews_this_week = 2 (today) + 2 (one_day_ago, three_days_ago) = 4
        # total_reviews_all_time = 2 (today) + 2 (this week not today) + 1 (older) = 5
        # overall_average_score: (s1.total_score_sum + s2.total_score_sum + s4_mastered.total_score_sum) / (s1.total_reviews + s2.total_reviews + s4_mastered.total_reviews)
        # (0.9 + 1.5 + 4.5) / (1 + 2 + 5) = 6.9 / 8 = 0.8625
        # sentences_mastered = 1 (s4_mastered)

        expected_stats = {
            "reviews_today": 2,
            "new_cards_reviewed_today": 1,
            "reviews_this_week": 4,
            "total_reviews_all_time": Review.objects.count(), # Should be 5 based on creation
            "overall_average_score": round((0.9 + 0.8 + 0.7 + 0.7 + 0.9) / 5, 4), # Corrected calculation: sum of scores / num_reviews
            "total_sentences": 4,
            "sentences_mastered": 1,
            "sentences_learned": 3,
            "percentage_learned": 75.0
        }
        self.assertEqual(response.data, expected_stats)

    # TODO: Add more granular tests: 
    # - Test with only new cards reviewed today
    # - Test with only review cards today
    # - Test with reviews exactly 7 days ago (should be counted in this week)
    # - Test average score calculation with more varied scores
    # - Test mastered calculation with edge cases (e.g. just meets criteria vs. exceeds)
    # - Test learned sentences when some sentences have no reviews at all.
    # - Test percentage learned when total_sentences is 0 (already covered by no_data, but good to keep in mind)

class SentenceListAPITests(APITestCase):
    def setUp(self):
        # Create test user and authenticate
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.test_user)
        
        Sentence.objects.all().delete()
        Review.objects.all().delete()
        self.sentences_url = "/api/flashcards/sentences/"
        self.today = timezone.now()

        # Create a batch of sentences for pagination and content testing
        # self.num_sentences will represent the number of unique concepts (CSV rows)
        self.num_unique_concepts = 15 # Let's reduce for faster tests, this will create 30 sentence objects
        created_sentences_count = 0

        for i in range(1, self.num_unique_concepts + 1):
            common_data = {
                'csv_number': 900 + i,
                'key_spanish_word': f"List Word {i}",
                'key_word_english_translation': f"List Translation {i}",
                'spanish_sentence_example': f"List Spanish Example {i}",
                'english_sentence_example': f"List English Example {i}",
                'total_reviews': i % 5, 
                'total_score_sum': (i % 5) * 0.8 if (i % 5 > 0) else 0.0, 
                'next_review_date': self.today.date() + timedelta(days=i),
                'is_learning': (i % 2 == 0),
                'interval_days': i % 7
            }

            # Create S2E card
            s2e_sentence = Sentence.objects.create(
                **common_data, 
                translation_direction='S2E',
                user=self.test_user
            )
            created_sentences_count += 1

            # Create E2S card (swap relevant fields)
            e2s_data = common_data.copy()
            e2s_data['key_spanish_word'] = common_data['key_word_english_translation']
            e2s_data['key_word_english_translation'] = common_data['key_spanish_word']
            e2s_data['spanish_sentence_example'] = common_data['english_sentence_example']
            e2s_data['english_sentence_example'] = common_data['spanish_sentence_example']
            
            e2s_sentence = Sentence.objects.create(
                **e2s_data,
                translation_direction='E2S',
                user=self.test_user
            )
            created_sentences_count += 1

            if i % 3 == 0: # Add a review for some sentences (add to both S2E and E2S for simplicity here)
                Review.objects.create(
                    sentence=s2e_sentence, 
                    user_score=0.9, 
                    review_timestamp=self.today - timedelta(days=i),
                    interval_at_review=0,
                    ease_factor_at_review=2.5
                )
                Review.objects.create(
                    sentence=e2s_sentence, 
                    user_score=0.8, # Slightly different score for E2S review
                    review_timestamp=self.today - timedelta(days=i), 
                    interval_at_review=0,
                    ease_factor_at_review=2.4
                )
        
        self.total_sentence_objects = created_sentences_count # Should be 2 * self.num_unique_concepts

    def test_list_sentences_paginated_default_size(self):
        """Test fetching the first page of sentences with default page size."""
        response = self.client.get(self.sentences_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # The view's pagination_class (StandardResultsSetPagination) has page_size = 100.
        # Since total_sentence_objects (e.g., 30) is less than page_size (100), all items should be returned.
        self.assertEqual(len(response.data['results']), self.total_sentence_objects) 
        self.assertEqual(response.data['count'], self.total_sentence_objects)

    def test_list_sentences_custom_page_size_and_navigation(self):
        """Test fetching with custom page size and navigating to the second page."""
        page_size = 10
        response = self.client.get(self.sentences_url, {'page_size': page_size, 'page': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['count'], self.total_sentence_objects)
        self.assertIsNotNone(response.data['next'])

    def test_list_sentences_last_page(self):
        """Test fetching the last page which might have fewer items, using a specific page_size."""
        page_size_to_test = 25 
        
        if self.total_sentence_objects == 0:
            response = self.client.get(self.sentences_url, {'page_size': page_size_to_test, 'page': 1})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data['results']), 0)
            self.assertEqual(response.data['count'], 0)
            self.assertIsNone(response.data['next'])
            self.assertIsNone(response.data['previous'])
            return

        num_pages = (self.total_sentence_objects + page_size_to_test - 1) // page_size_to_test 
        remaining_items = self.total_sentence_objects % page_size_to_test
        if remaining_items == 0 and self.total_sentence_objects > 0:
             remaining_items = page_size_to_test

        # Request the last page using the specific page_size_to_test
        response = self.client.get(self.sentences_url, {'page_size': page_size_to_test, 'page': num_pages})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), remaining_items)
        self.assertEqual(response.data['count'], self.total_sentence_objects) # Total count should still be all sentences

    def test_sentence_data_fields_in_list(self):
        """Verify that essential fields, including calculated ones, are present for a specific S2E card."""
        response = self.client.get(self.sentences_url, {'page_size': self.total_sentence_objects}) # Get all results
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        target_csv_number = 903
        target_direction = 'S2E'
        sentence_data = None
        for item in response.data['results']:
            if item['csv_number'] == target_csv_number and item['translation_direction'] == target_direction:
                sentence_data = item
                break
        
        self.assertIsNotNone(sentence_data, f"Sentence with CSV number {target_csv_number} and direction {target_direction} not found in list.")

        # For concept i=3 (csv_number=903):
        # total_reviews = 3 % 5 = 3
        # total_score_sum = 3 * 0.8 = 2.4 (for S2E)
        # average_score = 2.4 / 3 = 0.8
        # is_learning = (3 % 2 == 0) which is False
        # interval_days = 3 % 7 = 3
        # last_reviewed_date should exist because 3 % 3 == 0 (created in setUp)

        self.assertEqual(sentence_data['key_spanish_word'], "List Word 3") # For S2E
        self.assertIsNotNone(sentence_data['average_score'])
        self.assertAlmostEqual(sentence_data['average_score'], 0.8, places=2)
        self.assertIsNotNone(sentence_data['last_reviewed_date'])
        self.assertFalse(sentence_data['is_learning']) 
        self.assertEqual(sentence_data['total_reviews'], 3)
        self.assertEqual(sentence_data['interval_days'], 3)
        self.assertEqual(sentence_data['translation_direction'], 'S2E')

    # TODO: Add tests for filtering and sorting once implemented.
    # TODO: Test with no sentences in DB.

class SentenceDetailAPITests(APITestCase):
    def setUp(self):
        # Create test user and authenticate
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.test_user)
        
        Sentence.objects.all().delete()
        Review.objects.all().delete()
        self.today = timezone.now()

        self.s1_s2e = Sentence.objects.create(
            user=self.test_user,
            csv_number=1001,
            translation_direction='S2E',
            key_spanish_word="Detail Word 1 Spanish",
            key_word_english_translation="Detail Word 1 English",
            spanish_sentence_example="Spanish example for S1 S2E",
            english_sentence_example="English example for S1 S2E",
            total_reviews=2,
            total_score_sum=1.7, # avg 0.85
            next_review_date=self.today.date() + timedelta(days=5)
        )
        self.r1_s1_s2e = Review.objects.create(
            sentence=self.s1_s2e, user_score=0.8, review_timestamp=self.today - timedelta(days=2), 
            interval_at_review=1, ease_factor_at_review=2.5
        )
        self.r2_s1_s2e = Review.objects.create(
            sentence=self.s1_s2e, user_score=0.9, review_timestamp=self.today - timedelta(days=1), 
            user_comment_addon="Good progress on S2E!", interval_at_review=3, ease_factor_at_review=2.6
        )

        # Create E2S counterpart for s1
        self.s1_e2s = Sentence.objects.create(
            user=self.test_user,
            csv_number=1001, # Same csv_number
            translation_direction='E2S',
            key_spanish_word="Detail Word 1 English", # Swapped
            key_word_english_translation="Detail Word 1 Spanish", # Swapped
            spanish_sentence_example="English example for S1 E2S", # Swapped
            english_sentence_example="Spanish example for S1 E2S", # Swapped
            total_reviews=1, # Different review history for E2S version
            total_score_sum=0.7, # avg 0.7
            next_review_date=self.today.date() + timedelta(days=3) # Different next review
        )
        self.r1_s1_e2s = Review.objects.create(
            sentence=self.s1_e2s, user_score=0.7, review_timestamp=self.today - timedelta(days=4),
            user_comment_addon="E2S review.", interval_at_review=2, ease_factor_at_review=2.4
        )

        self.s2_no_reviews_s2e = Sentence.objects.create(
            user=self.test_user,
            csv_number=1002,
            translation_direction='S2E',
            key_spanish_word="Detail Word 2 No Reviews S2E", # More specific name
            key_word_english_translation="Detail Word 2 English Translation S2E",
            spanish_sentence_example="Spanish Example No Reviews S2E",
            english_sentence_example="English Example No Reviews S2E",
            total_reviews=0,
            total_score_sum=0.0,
            next_review_date=self.today.date()
        )
        
        self.s2_no_reviews_e2s = Sentence.objects.create(
            user=self.test_user,
            csv_number=1002,
            translation_direction='E2S',
            key_spanish_word="Detail Word 2 English Translation E2S", # Swapped and specific
            key_word_english_translation="Detail Word 2 No Reviews E2S", # Swapped and specific
            spanish_sentence_example="English Example No Reviews E2S", # Swapped
            english_sentence_example="Spanish Example No Reviews S2E", # Swapped
            total_reviews=0,
            total_score_sum=0.0,
            next_review_date=self.today.date()
        )

    def test_get_sentence_detail_exists_with_reviews(self):
        """Test fetching detail for an existing sentence with review history (S2E version)."""
        url = f'/api/flashcards/sentences/{self.s1_s2e.pk}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['sentence_id'], self.s1_s2e.pk)
        self.assertEqual(response.data['csv_number'], 1001)
        self.assertEqual(response.data['translation_direction'], 'S2E') # Verify direction
        self.assertAlmostEqual(response.data['average_score'], 0.85, places=2)
        self.assertIsNotNone(response.data['last_reviewed_date'])
        self.assertEqual(len(response.data['reviews']), 2)

        review_ids_in_response = {r['review_id'] for r in response.data['reviews']}
        self.assertIn(self.r1_s1_s2e.pk, review_ids_in_response)
        self.assertIn(self.r2_s1_s2e.pk, review_ids_in_response)
        
        r2_data = next(r for r in response.data['reviews'] if r['review_id'] == self.r2_s1_s2e.pk)
        self.assertEqual(r2_data['user_score'], 0.9)
        self.assertEqual(r2_data['user_comment_addon'], "Good progress on S2E!")

    def test_get_sentence_detail_e2s_with_reviews(self): # New test
        """Test fetching detail for an E2S sentence with its review history."""
        url = f'/api/flashcards/sentences/{self.s1_e2s.pk}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['sentence_id'], self.s1_e2s.pk)
        self.assertEqual(response.data['csv_number'], 1001)
        self.assertEqual(response.data['translation_direction'], 'E2S')
        self.assertAlmostEqual(response.data['average_score'], 0.7, places=2)
        self.assertEqual(len(response.data['reviews']), 1)
        self.assertEqual(response.data['reviews'][0]['review_id'], self.r1_s1_e2s.pk)
        self.assertEqual(response.data['reviews'][0]['user_comment_addon'], "E2S review.")

    def test_get_sentence_detail_exists_no_reviews(self):
        """Test fetching detail for an existing sentence with no review history (S2E version)."""
        url = f'/api/flashcards/sentences/{self.s2_no_reviews_s2e.pk}/' # Use s2e version
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['sentence_id'], self.s2_no_reviews_s2e.pk)
        self.assertEqual(response.data['csv_number'], 1002)
        self.assertEqual(response.data['translation_direction'], 'S2E') # Verify direction
        self.assertIsNone(response.data['average_score'])

    def test_get_sentence_detail_not_found(self):
        """Test fetching detail for a non-existent sentence ID."""
        non_existent_pk = self.s1_s2e.pk + self.s1_e2s.pk + self.s2_no_reviews_s2e.pk + self.s2_no_reviews_e2s.pk + 100 # A PK that surely doesn't exist
        url = f'/api/flashcards/sentences/{non_existent_pk}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CardAPITests(APITestCase):
    def setUp(self):
        # Create test user and authenticate
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.test_user)
        
        Card.objects.all().delete()
        CardReview.objects.all().delete()
        self.cards_url = "/api/flashcards/cards/"
        self.card_next_url = "/api/flashcards/cards/next-card/"
        self.card_submit_review_url = "/api/flashcards/cards/submit-review/"
        self.card_stats_url = "/api/flashcards/cards/statistics/"
        self.card_import_url = "/api/flashcards/cards/import/"

    def test_create_card_auto_creates_reverse_and_links(self):
        payload = {
            "front": "hola",
            "back": "hello",
            "language": "es",
            "tags": ["greeting"],
            "notes": "basic greeting",
            "source": "manual",
            "create_reverse": True
        }

        response = self.client.post(self.cards_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Card.objects.count(), 2)

        forward = Card.objects.get(front="hola", back="hello")
        reverse = Card.objects.get(front="hello", back="hola")

        self.assertEqual(forward.pair_id, reverse.pair_id)
        self.assertEqual(forward.linked_card_id, reverse.card_id)
        self.assertEqual(reverse.linked_card_id, forward.card_id)

    def test_card_next_card_prioritizes_due_review_cards(self):
        today = timezone.now().date()

        # Due review card
        due_review = Card.objects.create(
            front="front-review",
            back="back-review",
            is_learning=False,
            interval_days=10,
            next_review_date=today - timedelta(days=1),
            user=self.test_user
        )

        # Due learning card (should not be picked while a review due exists)
        Card.objects.create(
            front="front-learning",
            back="back-learning",
            is_learning=True,
            interval_days=0,
            next_review_date=today,
            user=self.test_user
        )

        response = self.client.get(self.card_next_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["card_id"], due_review.card_id)

    def test_card_submit_review_saves_typed_input(self):
        card = Card.objects.create(front="hola", back="hello", user=self.test_user)

        payload = {
            "card_id": card.card_id,
            "user_score": 0.9,
            "user_comment_addon": "felt good",
            "typed_input": "hello"
        }

        response = self.client.post(self.card_submit_review_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        card.refresh_from_db()
        self.assertEqual(card.total_reviews, 1)

        self.assertEqual(card.reviews.count(), 1)
        review = card.reviews.first()
        self.assertEqual(review.typed_input, "hello")

    def test_card_statistics_smoke(self):
        response = self.client.get(self.card_stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_cards", response.data)
        self.assertIn("total_reviews_all_time", response.data)

    def test_list_cards(self):
        """Test listing cards with pagination."""
        # Create some test cards
        Card.objects.create(front="test1", back="answer1", user=self.test_user)
        Card.objects.create(front="test2", back="answer2", user=self.test_user)
        Card.objects.create(front="test3", back="answer3", user=self.test_user)

        response = self.client.get(self.cards_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertGreaterEqual(len(response.data["results"]), 3)
        self.assertEqual(response.data["count"], 3)

    def test_list_cards_pagination(self):
        """Test card list pagination works correctly."""
        # Create more cards than default page size (100)
        for i in range(5):
            Card.objects.create(front=f"test{i}", back=f"answer{i}", user=self.test_user)

        response = self.client.get(self.cards_url, {'page': 1, 'page_size': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["count"], 5)
        self.assertIsNotNone(response.data.get("next"))

    def test_get_card_detail(self):
        """Test retrieving a single card's details."""
        card = Card.objects.create(
            front="test front",
            back="test back",
            language="es",
            tags=["test", "card"],
            notes="test notes",
            source="test source",
            user=self.test_user
        )

        url = f"{self.cards_url}{card.card_id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["card_id"], card.card_id)
        self.assertEqual(response.data["front"], "test front")
        self.assertEqual(response.data["back"], "test back")
        self.assertEqual(response.data["language"], "es")
        self.assertEqual(response.data["tags"], ["test", "card"])

    def test_update_card(self):
        """Test updating a card."""
        card = Card.objects.create(front="old front", back="old back", language="es", user=self.test_user)

        url = f"{self.cards_url}{card.card_id}/update/"
        payload = {
            "front": "new front",
            "back": "new back",
            "language": "de",
            "tags": ["updated"],
            "notes": "updated notes",
            "source": "updated source"
        }

        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        card.refresh_from_db()
        self.assertEqual(card.front, "new front")
        self.assertEqual(card.back, "new back")
        self.assertEqual(card.language, "de")
        self.assertEqual(card.tags, ["updated"])

    def test_update_card_partial(self):
        """Test partial update (PATCH) of a card."""
        card = Card.objects.create(front="front", back="back", language="es", user=self.test_user)

        url = f"{self.cards_url}{card.card_id}/update/"
        payload = {
            "front": "updated front"
        }

        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        card.refresh_from_db()
        self.assertEqual(card.front, "updated front")
        self.assertEqual(card.back, "back")  # Should remain unchanged

    def test_delete_card_without_linked_card(self):
        """Test deleting a card without a linked reverse card."""
        card = Card.objects.create(front="test", back="answer", user=self.test_user)

        url = f"{self.cards_url}{card.card_id}/delete/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Card.objects.filter(card_id=card.card_id).exists())

    def test_delete_card_with_linked_card(self):
        """Test deleting a card also deletes its linked reverse card."""
        forward = Card.objects.create(front="hola", back="hello", user=self.test_user)
        reverse = Card.objects.create(
            front="hello",
            back="hola",
            pair_id=forward.pair_id,
            user=self.test_user
        )
        forward.linked_card = reverse
        reverse.linked_card = forward
        forward.save()
        reverse.save()

        url = f"{self.cards_url}{forward.card_id}/delete/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(Card.objects.filter(card_id=forward.card_id).exists())
        self.assertFalse(Card.objects.filter(card_id=reverse.card_id).exists())

    def test_import_cards_preview_only(self):
        """Test preview mode of import endpoint."""
        csv_content = "front,back,language\nhola,hello,es\nadiós,goodbye,es"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'test.csv'

        # Preview mode can work with empty columns to just get column list
        form_data = {
            'file': csv_file,
            'front_column': '',
            'back_column': '',
            'preview_only': 'true'
        }

        response = self.client.post(self.card_import_url, form_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("columns", response.data)
        self.assertIn("preview", response.data)
        self.assertIn("total_rows", response.data)
        self.assertEqual(response.data["total_rows"], 2)
        self.assertEqual(Card.objects.count(), 0)  # No cards should be created in preview mode

        # Preview with columns selected should show preview data
        csv_file2 = BytesIO(csv_content.encode('utf-8'))
        csv_file2.name = 'test2.csv'
        form_data2 = {
            'file': csv_file2,
            'front_column': 'front',
            'back_column': 'back',
            'preview_only': 'true'
        }

        response2 = self.client.post(self.card_import_url, form_data2, format='multipart')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response2.data["preview"]), 0)

    def test_import_cards_success(self):
        """Test successful card import."""
        csv_content = "front,back,language,tags\nhola,hello,es,greeting\nadiós,goodbye,es,greeting"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'test.csv'

        form_data = {
            'file': csv_file,
            'front_column': 'front',
            'back_column': 'back',
            'language': 'es',
            'create_reverse': 'true',
            'preview_only': 'false'
        }

        response = self.client.post(self.card_import_url, form_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("created_count", response.data)
        self.assertEqual(response.data["created_count"], 2)  # 2 rows = 2 forward cards
        self.assertEqual(Card.objects.count(), 4)  # 2 forward + 2 reverse cards

        # Verify cards were created correctly
        hola_card = Card.objects.get(front="hola", back="hello")
        self.assertEqual(hola_card.language, "es")
        self.assertIsNotNone(hola_card.linked_card)

    def test_import_cards_without_reverse(self):
        """Test importing cards without creating reverse cards."""
        csv_content = "front,back\nhola,hello\nadiós,goodbye"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'test.csv'

        form_data = {
            'file': csv_file,
            'front_column': 'front',
            'back_column': 'back',
            'create_reverse': 'false',
            'preview_only': 'false'
        }

        response = self.client.post(self.card_import_url, form_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Card.objects.count(), 2)  # Only forward cards

    def test_import_cards_missing_columns(self):
        """Test import fails when required columns are missing."""
        csv_content = "front,back\nhola,hello"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'test.csv'

        form_data = {
            'file': csv_file,
            'front_column': 'nonexistent',
            'back_column': 'back',
            'preview_only': 'false'
        }

        response = self.client.post(self.card_import_url, form_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_import_cards_no_file(self):
        """Test import fails when no file is provided."""
        form_data = {
            'front_column': 'front',
            'back_column': 'back',
            'preview_only': 'false'
        }

        response = self.client.post(self.card_import_url, form_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_import_cards_tsv_format(self):
        """Test importing TSV format."""
        tsv_content = "front\tback\tlanguage\nhola\thello\tes"
        tsv_file = BytesIO(tsv_content.encode('utf-8'))
        tsv_file.name = 'test.tsv'

        form_data = {
            'file': tsv_file,
            'front_column': 'front',
            'back_column': 'back',
            'delimiter': '\t',
            'create_reverse': 'false',  # Don't create reverse card for this test
            'preview_only': 'false'
        }

        response = self.client.post(self.card_import_url, form_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Card.objects.count(), 1)

    def test_import_cards_with_optional_fields(self):
        """Test import with optional fields like tags, notes, source."""
        csv_content = "front,back,tags,notes,source\nhola,hello,tag1 tag2,some notes,manual"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'test.csv'

        form_data = {
            'file': csv_file,
            'front_column': 'front',
            'back_column': 'back',
            'preview_only': 'false'
        }

        response = self.client.post(self.card_import_url, form_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        card = Card.objects.get(front="hola")
        self.assertEqual(card.back, "hello")
        self.assertEqual(card.notes, "some notes")
        self.assertEqual(card.source, "manual")
        # Tags are parsed from comma-separated values in CSV
        if card.tags:
            self.assertIn("tag1", card.tags or [])

    def test_import_cards_empty_rows_handled(self):
        """Test that empty rows are handled gracefully."""
        csv_content = "front,back\nhola,hello\n,\nadiós,goodbye"
        csv_file = BytesIO(csv_content.encode('utf-8'))
        csv_file.name = 'test.csv'

        form_data = {
            'file': csv_file,
            'front_column': 'front',
            'back_column': 'back',
            'preview_only': 'false'
        }

        response = self.client.post(self.card_import_url, form_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Should create 2 cards (hola and adiós), skip empty row
        self.assertEqual(response.data["created_count"], 2)
        self.assertGreater(response.data["error_count"], 0)  # Should have errors for empty row

    def test_update_card_readonly_fields_ignored(self):
        """Test that readonly fields cannot be updated."""
        card = Card.objects.create(front="front", back="back", user=self.test_user)
        original_pair_id = card.pair_id
        original_card_id = card.card_id

        url = f"{self.cards_url}{card.card_id}/update/"
        payload = {
            "front": "updated",
            "card_id": 99999,  # Should be ignored
            "pair_id": "new-uuid"  # Should be ignored
        }

        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        card.refresh_from_db()
        self.assertEqual(card.front, "updated")
        self.assertEqual(card.card_id, original_card_id)  # Should not change
        self.assertEqual(str(card.pair_id), str(original_pair_id))  # Should not change

    def test_delete_nonexistent_card(self):
        """Test deleting a card that doesn't exist."""
        url = f"{self.cards_url}99999/delete/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
