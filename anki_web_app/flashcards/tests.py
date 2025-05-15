from django.test import TestCase
import os
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from flashcards.models import Sentence

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
