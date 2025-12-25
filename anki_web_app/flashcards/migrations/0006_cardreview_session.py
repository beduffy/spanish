# Generated migration: Add session field to CardReview

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flashcards', '0005_studysession_sessionactivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='cardreview',
            name='session',
            field=models.ForeignKey(
                blank=True,
                help_text='Study session this review belongs to',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='card_reviews',
                to='flashcards.studysession'
            ),
        ),
    ]
