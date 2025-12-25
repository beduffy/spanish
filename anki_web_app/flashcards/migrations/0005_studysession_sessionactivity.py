# Generated manually for Phase 5: Study Session tracking

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('flashcards', '0004_card_user_sentence_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudySession',
            fields=[
                ('session_id', models.AutoField(primary_key=True, serialize=False)),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now, help_text='When the session started')),
                ('end_time', models.DateTimeField(blank=True, help_text='When the session ended (null if active)', null=True)),
                ('last_activity_time', models.DateTimeField(default=django.utils.timezone.now, help_text='Last recorded activity timestamp')),
                ('is_active', models.BooleanField(default=True, help_text='True if session is still active')),
                ('user', models.ForeignKey(help_text='User who owns this session', on_delete=django.db.models.deletion.CASCADE, related_name='study_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Study Session',
                'verbose_name_plural': 'Study Sessions',
                'ordering': ['-start_time'],
            },
        ),
        migrations.CreateModel(
            name='SessionActivity',
            fields=[
                ('activity_id', models.AutoField(primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, help_text='When this activity occurred')),
                ('session', models.ForeignKey(help_text='The study session this activity belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='session_activities', to='flashcards.studysession')),
            ],
            options={
                'verbose_name': 'Session Activity',
                'verbose_name_plural': 'Session Activities',
                'ordering': ['timestamp'],
            },
        ),
    ]
