from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from flashcards.models import Card

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a test user for local development. Username: testuser, Email: test@example.com'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='testuser',
            help='Username for the test user (default: testuser)',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='Email for the test user (default: test@example.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='Password for the test user (default: testpass123)',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists. Skipping creation.'))
            user = User.objects.get(username=username)
        else:
            # Create user
            # Note: For Supabase auth, username should match Supabase user ID (sub claim)
            # But for local testing, we'll create a regular Django user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name='Test',
                last_name='User',
            )
            self.stdout.write(self.style.SUCCESS(f'Created test user: {username} ({email})'))

        # Create a sample card for the test user
        if not Card.objects.filter(user=user).exists():
            Card.objects.create(
                user=user,
                front='Hello',
                back='Hola',
                notes='Test card for local development',
                next_review_date=timezone.now().date(),
                is_learning=True,
                interval_days=0,
            )
            self.stdout.write(self.style.SUCCESS(f'Created sample card for {username}'))

        self.stdout.write(self.style.SUCCESS('\nTest user credentials:'))
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  Email: {email}')
        self.stdout.write(f'  Password: {password}')
        self.stdout.write(self.style.WARNING('\nNote: For Supabase authentication, you need to:'))
        self.stdout.write('  1. Sign up at http://localhost:8080/login')
        self.stdout.write('  2. Or create a user in Supabase Dashboard')
        self.stdout.write('  3. The Django user will be auto-created when you authenticate with Supabase')
