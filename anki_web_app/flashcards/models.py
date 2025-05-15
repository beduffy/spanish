from django.db import models
from django.utils import timezone


class Sentence(models.Model):
    sentence_id = models.AutoField(primary_key=True)
    csv_number = models.IntegerField(unique=True, help_text="Original number from CSV for reference")
    key_spanish_word = models.TextField()
    key_word_english_translation = models.TextField()
    spanish_sentence_example = models.TextField()
    english_sentence_example = models.TextField()
    base_comment = models.TextField(blank=True, null=True, help_text="Initial comment from CSV")
    ai_explanation = models.TextField(blank=True, null=True, help_text="Stores concatenated/chosen AI explanations")
    creation_date = models.DateTimeField(default=timezone.now, help_text="Timestamp of import")
    last_modified_date = models.DateTimeField(auto_now=True, help_text="Timestamp of last update to card or SRS data")
    ease_factor = models.FloatField(default=2.5, help_text="For SM2-like algorithm")
    interval_days = models.IntegerField(default=0, help_text="Current interval in days; 0 for new/learning cards")
    next_review_date = models.DateField(default=timezone.now, help_text="Date for next scheduled review")
    is_learning = models.BooleanField(default=True, help_text="True if card is in learning phase, False if graduated/reviewing")
    consecutive_correct_reviews = models.IntegerField(default=0, help_text="Number of consecutive reviews with score > 0.8")
    total_reviews = models.IntegerField(default=0, help_text="Counter for how many times this card has been reviewed")
    total_score_sum = models.FloatField(default=0.0, help_text="Sum of all scores for this card, to calculate average")

    def __str__(self):
        return f"{self.csv_number}: {self.key_spanish_word} - {self.spanish_sentence_example[:50]}..."

    class Meta:
        ordering = ['csv_number']
        verbose_name = "Sentence Card"
        verbose_name_plural = "Sentence Cards"


class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    sentence = models.ForeignKey(Sentence, on_delete=models.CASCADE, related_name='reviews')
    review_timestamp = models.DateTimeField(default=timezone.now, help_text="Timestamp of the review")
    user_score = models.FloatField(help_text="Score given by user, 0.0 to 1.0")
    user_comment_addon = models.TextField(blank=True, null=True, help_text="Additional comment made by user during this specific review")
    interval_at_review = models.IntegerField(help_text="The interval setting for the card before this review took place")
    ease_factor_at_review = models.FloatField(help_text="The ease factor for the card before this review took place")

    def __str__(self):
        return f"Review for '{self.sentence.key_spanish_word}' at {self.review_timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-review_timestamp']
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
