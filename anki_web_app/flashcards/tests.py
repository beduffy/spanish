from django.test import TestCase
import os
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from flashcards.models import Sentence, Review, LEARNING_STEPS_DAYS, GRADUATING_INTERVAL_DAYS, LAPSE_INTERVAL_DAYS, MIN_EASE_FACTOR
from datetime import timedelta

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
