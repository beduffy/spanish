from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from anki_web_app.flashcards.models import Sentence, Review

class Command(BaseCommand):
    help = 'Seeds the database with specific data for E2E testing.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Seeding database for E2E tests...'))

        # Clear existing data
        Review.objects.all().delete()
        Sentence.objects.all().delete()
        self.stdout.write(self.style.WARNING('Cleared existing Sentences and Reviews.'))

        # Get today's date
        today = timezone.now().date()

        # Create Sentences
        # Card 1: S2E, learning, due today
        Sentence.objects.create(
            csv_number=1001,
            translation_direction='S2E',
            key_spanish_word='Hola',
            key_word_english_translation='Hello',
            spanish_sentence_example='Hola, ¿cómo estás?',
            english_sentence_example='Hello, how are you?',
            base_comment='Greeting',
            next_review_date=today,
            is_learning=True,
            interval_days=0 
        )

        # Card 2: E2S, learning, due today
        Sentence.objects.create(
            csv_number=1002,
            translation_direction='E2S',
            key_spanish_word='Adiós',
            key_word_english_translation='Goodbye',
            spanish_sentence_example='Adiós, hasta luego.',
            english_sentence_example='Goodbye, see you later.',
            base_comment='Farewell',
            next_review_date=today,
            is_learning=True,
            interval_days=1 # e.g. second learning step
        )

        # Card 3: S2E, graduated, due today
        Sentence.objects.create(
            csv_number=1003,
            translation_direction='S2E',
            key_spanish_word='Gracias',
            key_word_english_translation='Thank you',
            spanish_sentence_example='Muchas gracias por tu ayuda.',
            english_sentence_example='Thank you very much for your help.',
            base_comment='Gratitude',
            next_review_date=today,
            is_learning=False,
            ease_factor=2.5,
            interval_days=5
        )

        # Card 4: S2E, graduated, due in the future
        Sentence.objects.create(
            csv_number=1004,
            translation_direction='S2E',
            key_spanish_word='Por favor',
            key_word_english_translation='Please',
            spanish_sentence_example='¿Me puedes pasar la sal, por favor?',
            english_sentence_example='Can you pass me the salt, please?',
            base_comment='Request',
            next_review_date=today + timedelta(days=10),
            is_learning=False,
            ease_factor=2.6,
            interval_days=10
        )

        # Card 5: E2S, graduated, due in the past (so also due today)
        Sentence.objects.create(
            csv_number=1005,
            translation_direction='E2S',
            key_spanish_word='Agua',
            key_word_english_translation='Water',
            spanish_sentence_example='Necesito un vaso de agua.',
            english_sentence_example='I need a glass of water.',
            base_comment='Basic need',
            next_review_date=today - timedelta(days=2),
            is_learning=False,
            ease_factor=2.3,
            interval_days=3 
        )
        
        # Card 6: S2E, learning, future (not due)
        Sentence.objects.create(
            csv_number=1006,
            translation_direction='S2E',
            key_spanish_word='Libro',
            key_word_english_translation='Book',
            spanish_sentence_example='Estoy leyendo un libro interesante.',
            english_sentence_example='I am reading an interesting book.',
            base_comment='Reading material',
            next_review_date=today + timedelta(days=2),
            is_learning=True,
            interval_days=2 # e.g. second learning step
        )


        self.stdout.write(self.style.SUCCESS(f'Created {Sentence.objects.count()} sentences for E2E testing.'))
        self.stdout.write(self.style.SUCCESS('E2E test data seeding complete.')) 