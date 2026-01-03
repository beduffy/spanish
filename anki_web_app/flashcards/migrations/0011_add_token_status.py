# Generated manually for TokenStatus model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('flashcards', '0010_add_lesson_progress_tracking'),
    ]

    operations = [
        migrations.CreateModel(
            name='TokenStatus',
            fields=[
                ('status_id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('unknown', 'Unknown'), ('known', 'Known')], default='unknown', help_text='Whether the user knows this word', max_length=10)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('token', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='statuses', to='flashcards.token')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='token_statuses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Token Status',
                'verbose_name_plural': 'Token Statuses',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='tokenstatus',
            index=models.Index(fields=['user', 'status'], name='flashcards__user_id_status_idx'),
        ),
        migrations.AddIndex(
            model_name='tokenstatus',
            index=models.Index(fields=['token', 'status'], name='flashcards__token_id_status_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='tokenstatus',
            unique_together={('user', 'token')},
        ),
    ]
