import csv
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from flashcards.models import Sentence
import os

class Command(BaseCommand):
    help = 'Imports sentences from a specified CSV file into the Sentence table'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The path to the CSV file to import.')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file_path']

        if not os.path.exists(csv_file_path):
            raise CommandError(f'File "{csv_file_path}" does not exist')

        self.stdout.write(self.style.SUCCESS(f'Starting import from "{csv_file_path}"'))

        # Keep track of imported sentences to avoid duplicates if script is run multiple times
        # based on csv_number
        existing_csv_numbers = set(Sentence.objects.values_list('csv_number', flat=True))
        imported_count = 0
        skipped_count = 0

        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Verify necessary columns are present
                required_columns = ['Number', 'Spanish Word', 'English Translation', 'Spanish Example', 'English Example']
                if not all(col in reader.fieldnames for col in required_columns):
                    missing = [col for col in required_columns if col not in reader.fieldnames]
                    raise CommandError(f"Missing required columns in CSV: {', '.join(missing)}")

                for row_num, row in enumerate(reader, start=2): # start=2 because of header row
                    try:
                        csv_number = int(row['Number'])
                        if csv_number in existing_csv_numbers:
                            self.stdout.write(self.style.WARNING(f'Skipping already imported sentence with CSV Number: {csv_number}'))
                            skipped_count += 1
                            continue

                        key_spanish_word = row['Spanish Word']
                        key_word_english_translation = row['English Translation']
                        spanish_sentence_example = row['Spanish Example']
                        english_sentence_example = row['English Example']
                        base_comment = row.get('Comment') # Changed: Allow None if column missing, or actual value (empty string if cell is empty)
                        
                        # Concatenate AI explanations if they exist, otherwise leave as None
                        chat_gpt_explanation = row.get('Chat GPTs explanation', '').strip()
                        gemini_explanation = row.get('Gemini explanation', '').strip()
                        ai_explanation = None
                        if chat_gpt_explanation and gemini_explanation:
                            ai_explanation = f"ChatGPT: {chat_gpt_explanation}\nGemini: {gemini_explanation}"
                        elif chat_gpt_explanation:
                            ai_explanation = chat_gpt_explanation
                        elif gemini_explanation:
                            ai_explanation = gemini_explanation

                        Sentence.objects.create(
                            csv_number=csv_number,
                            key_spanish_word=key_spanish_word,
                            key_word_english_translation=key_word_english_translation,
                            spanish_sentence_example=spanish_sentence_example,
                            english_sentence_example=english_sentence_example,
                            base_comment=base_comment, # Changed: Directly pass the value
                            ai_explanation=ai_explanation,
                            # SRS defaults are set in the model definition
                            # (ease_factor, interval_days, next_review_date, is_learning, consecutive_correct_reviews)
                            # creation_date and last_modified_date also have defaults or auto_now
                        )
                        existing_csv_numbers.add(csv_number) # Add to set after successful creation
                        imported_count += 1
                    except ValueError as e:
                        self.stderr.write(self.style.ERROR(f'Error processing row {row_num}: {e}. Row data: {row}'))
                    except KeyError as e:
                        self.stderr.write(self.style.ERROR(f'Missing expected column in row {row_num}: {e}. Row data: {row}'))
                        
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported_count} new sentences.'))
            if skipped_count > 0:
                self.stdout.write(self.style.WARNING(f'Skipped {skipped_count} already existing sentences.'))

        except FileNotFoundError:
            raise CommandError(f'File "{csv_file_path}" not found')
        except Exception as e:
            raise CommandError(f'An error occurred: {e}') 