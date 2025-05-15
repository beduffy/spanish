from django.test import TestCase
import os
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from flashcards.models import Sentence, Review, LEARNING_STEPS_DAYS, GRADUATING_INTERVAL_DAYS, LAPSE_INTERVAL_DAYS, MIN_EASE_FACTOR
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status

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
 # Test with trailing commas for robustness
        )
        temp_csv_file = self._create_temp_csv(csv_content)

        call_command('import_csv', temp_csv_file)

        self.assertEqual(Sentence.objects.count(), 3)

        s1 = Sentence.objects.get(csv_number=1)
        self.assertEqual(s1.key_spanish_word, 'De')
        self.assertEqual(s1.key_word_english_translation, 'From')
        self.assertEqual(s1.spanish_sentence_example, 'Él es de la ciudad de Nueva York.')
        self.assertEqual(s1.english_sentence_example, 'He is from New York City.')
        self.assertEqual(s1.base_comment, 'Old base comment')
        self.assertEqual(s1.ai_explanation, "ChatGPT: GPT expl 1\nGemini: Gemini expl 1")
        self.assertEqual(s1.ease_factor, 2.5) # Default
        self.assertEqual(s1.interval_days, 0) # Default
        self.assertTrue(s1.is_learning) # Default
        self.assertEqual(s1.consecutive_correct_reviews, 0) # Default
        self.assertEqual(s1.next_review_date, timezone.now().date())

        s2 = Sentence.objects.get(csv_number=2)
        self.assertEqual(s2.key_spanish_word, 'Que')
        self.assertEqual(s2.english_sentence_example, 'That is the girl that I like.')
        self.assertEqual(s2.base_comment, 'Another comment')
        self.assertIsNone(s2.ai_explanation) # Only one AI explanation missing

        s3 = Sentence.objects.get(csv_number=3)
        self.assertEqual(s3.key_spanish_word, 'No')
        self.assertEqual(s3.base_comment, '') # Empty comment
        self.assertIsNone(s3.ai_explanation) # Both AI explanations missing


    def test_import_csv_duplicates_skipped(self):
        # First import
        csv_content_initial = (
            "Number,Spanish Word,English Translation,Spanish Example,English Example\n"
            "10,Hola,Hello,Hola Mundo,Hello World\n"
        )
        temp_csv_file_initial = self._create_temp_csv(csv_content_initial)
        call_command('import_csv', temp_csv_file_initial)
        self.assertEqual(Sentence.objects.count(), 1)

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
        
        self.assertEqual(Sentence.objects.count(), 2) # Only one new sentence should be added
        self.assertTrue(Sentence.objects.filter(csv_number=10).exists())
        self.assertTrue(Sentence.objects.filter(csv_number=11).exists())
        
        output = out.getvalue()
        self.assertIn("Skipping already imported sentence with CSV Number: 10", output)
        self.assertIn("Successfully imported 1 new sentences.", output) # Check specific message for new imports
        self.assertIn("Skipped 1 already existing sentences.", output)


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
        self.assertIn("Successfully imported 0 new sentences.", out.getvalue())

class SRSLogicTests(TestCase):
    def _create_sentence(self, csv_number=100, key_spanish_word="Test Word", 
                           ease_factor=2.5, interval_days=0, 
                           is_learning=True, consecutive_correct_reviews=0,
                           next_review_date=None, total_reviews=0, total_score_sum=0.0):
        if next_review_date is None:
            next_review_date = timezone.now().date()
        
        # Delete if exists to ensure clean slate for specific csv_number in tests
        Sentence.objects.filter(csv_number=csv_number).delete()
        
        return Sentence.objects.create(
            csv_number=csv_number,
            key_spanish_word=key_spanish_word,
            key_word_english_translation="Test Translation",
            spanish_sentence_example="Test Spanish Example",
            english_sentence_example="Test English Example",
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
        
        # This method doesn't exist yet, so this test will error out initially
        sentence.process_review(user_score=0.95, review_comment="Perfect!") 

        self.assertEqual(sentence.interval_days, 1, "Interval should be 1 day after first learning pass")
        self.assertAlmostEqual(sentence.ease_factor, original_ef + 0.1, delta=0.01, msg="EF should increase for perfect score")
        self.assertTrue(sentence.is_learning, "Should still be in learning phase")
        self.assertEqual(sentence.consecutive_correct_reviews, 1, "Consecutive good scores should be 1")
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
        self.assertEqual(sentence.consecutive_correct_reviews, 0, "Score 0.7 is not > 0.8 for mastery tracking")
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
                           ease_factor=2.5, interval_days=0, 
                           is_learning=True, consecutive_correct_reviews=0,
                           next_review_date=None, total_reviews=0, total_score_sum=0.0,
                           spanish_sentence_example="Test Spanish Example API", 
                           english_sentence_example="Test English Example API",
                           key_word_english_translation="Test Translation API",
                           base_comment="Base comment API",
                           ai_explanation="AI Explanation API"):
        if next_review_date is None:
            next_review_date = timezone.now().date()
        
        # Delete if exists to ensure clean slate for specific csv_number in tests
        Sentence.objects.filter(csv_number=csv_number).delete()
        
        return Sentence.objects.create(
            csv_number=csv_number,
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
            total_score_sum=total_score_sum
        )

    def setUp(self):
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
                           ease_factor=2.5, interval_days=0, 
                           is_learning=True, consecutive_correct_reviews=0,
                           next_review_date=None, base_comment="Initial comment.",
                           total_reviews=0, total_score_sum=0.0):
        if next_review_date is None:
            next_review_date = timezone.now().date()
        
        Sentence.objects.filter(csv_number=csv_number).delete() # Ensure clean slate
        
        return Sentence.objects.create(
            csv_number=csv_number,
            key_spanish_word=key_spanish_word,
            key_word_english_translation="Submit Translation",
            spanish_sentence_example="Submit Spanish Example",
            english_sentence_example="Submit English Example",
            base_comment=base_comment,
            ease_factor=ease_factor,
            interval_days=interval_days,
            is_learning=is_learning,
            consecutive_correct_reviews=consecutive_correct_reviews,
            next_review_date=next_review_date,
            total_reviews=total_reviews,
            total_score_sum=total_score_sum
        )

    def setUp(self):
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
