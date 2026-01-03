# Generated manually for progress tracking feature

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0009_add_lemma_to_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='status',
            field=models.CharField(
                choices=[
                    ('not_started', 'Not Started'),
                    ('in_progress', 'In Progress'),
                    ('completed', 'Completed'),
                ],
                default='not_started',
                help_text='Reading progress status',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='lesson',
            name='words_read',
            field=models.IntegerField(default=0, help_text='Number of words/tokens read'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='reading_time_seconds',
            field=models.IntegerField(default=0, help_text='Total seconds spent reading'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='last_read_at',
            field=models.DateTimeField(blank=True, help_text='Last time lesson was read', null=True),
        ),
        migrations.AddField(
            model_name='lesson',
            name='completed_at',
            field=models.DateTimeField(blank=True, help_text='When lesson was marked as completed', null=True),
        ),
    ]
