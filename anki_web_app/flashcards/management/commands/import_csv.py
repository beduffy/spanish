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

        # Keep track of imported sentences to avoid duplicates
        # based on (csv_number, translation_direction) tuples
        existing_sentence_tuples = set(
            Sentence.objects.values_list('csv_number', 'translation_direction')
        )
        imported_s2e_count = 0
        imported_e2s_count = 0
        skipped_s2e_count = 0
        skipped_e2s_count = 0

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
                        
                        # Common data for both directions
                        base_comment_val = row.get('Comment')
                        chat_gpt_explanation = row.get('Chat GPTs explanation', '').strip()
                        gemini_explanation = row.get('Gemini explanation', '').strip()
                        ai_explanation_val = None
                        if chat_gpt_explanation and gemini_explanation:
                            ai_explanation_val = f"ChatGPT: {chat_gpt_explanation}\nGemini: {gemini_explanation}"
                        elif chat_gpt_explanation:
                            ai_explanation_val = chat_gpt_explanation
                        elif gemini_explanation:
                            ai_explanation_val = gemini_explanation

                        # Data for S2E card
                        s2e_tuple = (csv_number, 'S2E')
                        if s2e_tuple in existing_sentence_tuples:
                            self.stdout.write(self.style.WARNING(f'Skipping already imported S2E sentence with CSV Number: {csv_number}'))
                            skipped_s2e_count += 1
                        else:
                            Sentence.objects.create(
                                csv_number=csv_number,
                                translation_direction='S2E',
                                key_spanish_word=row['Spanish Word'],
                                key_word_english_translation=row['English Translation'],
                                spanish_sentence_example=row['Spanish Example'],
                                english_sentence_example=row['English Example'],
                                base_comment=base_comment_val,
                                ai_explanation=ai_explanation_val,
                            )
                            existing_sentence_tuples.add(s2e_tuple)
                            imported_s2e_count += 1

                        # Data for E2S card
                        e2s_tuple = (csv_number, 'E2S')
                        if e2s_tuple in existing_sentence_tuples:
                            self.stdout.write(self.style.WARNING(f'Skipping already imported E2S sentence with CSV Number: {csv_number}'))
                            skipped_e2s_count += 1
                        else:
                            Sentence.objects.create(
                                csv_number=csv_number,
                                translation_direction='E2S',
                                # For E2S, the 'key_spanish_word' field will store the English key word/phrase
                                # and 'key_word_english_translation' will store the Spanish one.
                                # The prompt sentence is English, answer is Spanish.
                                key_spanish_word=row['English Translation'], # English key word is the prompt's key
                                key_word_english_translation=row['Spanish Word'], # Spanish key word is the answer's key
                                spanish_sentence_example=row['English Example'], # English sentence is the prompt
                                english_sentence_example=row['Spanish Example'], # Spanish sentence is the answer
                                base_comment=base_comment_val,
                                ai_explanation=ai_explanation_val,
                            )
                            existing_sentence_tuples.add(e2s_tuple)
                            imported_e2s_count += 1
                            
                    except ValueError as e:
                        self.stderr.write(self.style.ERROR(f'Error processing row {row_num}: {e}. Row data: {row}'))
                    except KeyError as e:
                        self.stderr.write(self.style.ERROR(f'Missing expected column in row {row_num}: {e}. Row data: {row}'))
                        
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {imported_s2e_count} new S2E sentences and {imported_e2s_count} new E2S sentences.'))
            if skipped_s2e_count > 0 or skipped_e2s_count > 0:
                self.stdout.write(self.style.WARNING(f'Skipped {skipped_s2e_count} S2E and {skipped_e2s_count} E2S already existing sentences.'))

        except FileNotFoundError:
            raise CommandError(f'File "{csv_file_path}" not found')
        except Exception as e:
            raise CommandError(f'An error occurred: {e}') 