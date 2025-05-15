from django.db import models
from django.utils import timezone
from datetime import timedelta # Ensure timedelta is imported

# Constants for SRS logic
INITIAL_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3
GRADUATING_INTERVAL_DAYS = 4 # First interval after graduating from learning steps
LAPSE_INTERVAL_DAYS = 0 # Interval when a review card lapses (back to learning step 1)
LEARNING_STEPS_DAYS = [1, 3] # Intervals for learning steps: 1 day, then 3 days

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
    ease_factor = models.FloatField(default=INITIAL_EASE_FACTOR, help_text="For SM2-like algorithm")
    interval_days = models.IntegerField(default=0, help_text="Current interval in days; 0 for new/learning cards")
    next_review_date = models.DateField(default=timezone.now, help_text="Date for next scheduled review")
    is_learning = models.BooleanField(default=True, help_text="True if card is in learning phase, False if graduated/reviewing")
    consecutive_correct_reviews = models.IntegerField(default=0, help_text="Number of consecutive reviews with score > 0.8")
    total_reviews = models.IntegerField(default=0, help_text="Counter for how many times this card has been reviewed")
    total_score_sum = models.FloatField(default=0.0, help_text="Sum of all scores for this card, to calculate average")

    def __str__(self):
        return f"{self.csv_number}: {self.key_spanish_word} - {self.spanish_sentence_example[:50]}..."

    def _get_quality_from_score(self, score):
        if score >= 0.9:
            return 5
        if score >= 0.8:
            return 4
        if score >= 0.6:
            return 3
        if score >= 0.4:
            return 2
        if score >= 0.2:
            return 1
        return 0

    def process_review(self, user_score, review_comment=None):
        # Store current state for the Review object
        interval_before_review = self.interval_days
        ease_factor_before_review = self.ease_factor

        q = self._get_quality_from_score(user_score)

        # Update consecutive_correct_reviews (for mastery definition: score > 0.8)
        if user_score > 0.8: # Corresponds to q >= 4
            self.consecutive_correct_reviews += 1
        else:
            self.consecutive_correct_reviews = 0

        if self.is_learning:
            if q >= 3: # Passed a learning step
                current_step_index = -1
                if self.interval_days == 0: # Just starting or failed previous step
                    current_step_index = -1 # Will move to LEARNING_STEPS_DAYS[0]
                elif self.interval_days == LEARNING_STEPS_DAYS[0]:
                    current_step_index = 0
                elif self.interval_days == LEARNING_STEPS_DAYS[1]:
                    current_step_index = 1
                
                next_step_index = current_step_index + 1
                if next_step_index < len(LEARNING_STEPS_DAYS):
                    self.interval_days = LEARNING_STEPS_DAYS[next_step_index]
                else: # Graduated from learning steps
                    self.is_learning = False
                    self.interval_days = GRADUATING_INTERVAL_DAYS
            else: # Failed a learning step
                self.interval_days = 0 # Reset to the first learning step (due now or next day)
        else: # Reviewing a graduated card
            if q >= 3: # Correct recall
                if self.interval_days == 0: # Should not happen for graduated card, but as a safeguard (e.g. lapsed and q>=3 somehow)
                    self.interval_days = GRADUATING_INTERVAL_DAYS 
                else:
                    self.interval_days = round(self.interval_days * self.ease_factor)
            else: # Incorrect recall (Lapse)
                self.is_learning = True
                self.interval_days = LAPSE_INTERVAL_DAYS # Reset to first learning step
                self.ease_factor = max(MIN_EASE_FACTOR, self.ease_factor - 0.20) # Penalize EF

        # Update Ease Factor if quality was good enough (q >= 3)
        if q >= 3:
            new_ef = self.ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
            self.ease_factor = max(MIN_EASE_FACTOR, new_ef)
        # If q < 3 and not learning (a lapse), EF was already penalized. If learning and q<3, EF typically isn't changed much.

        # Ensure interval_days is at least 1 if not in the very first learning step (interval 0)
        if self.interval_days == 0 and not (self.is_learning and q < 3): # if it's a pass, first step is 1 day.
             pass # Interval remains 0 if failed and reset to first step
        elif self.interval_days < 1 and self.is_learning and q >=3 : # First successful step makes interval 1 if it was 0
             if interval_before_review == 0 : self.interval_days = LEARNING_STEPS_DAYS[0]
        elif self.interval_days < 1 and not self.is_learning: # Graduated cards should have interval >=1
            self.interval_days = 1 


        self.next_review_date = timezone.now().date() + timedelta(days=self.interval_days)
        
        # Update totals
        self.total_reviews += 1
        self.total_score_sum += user_score
        
        self.save()

        # Create Review object
        Review.objects.create(
            sentence=self,
            user_score=user_score,
            user_comment_addon=review_comment,
            interval_at_review=interval_before_review,
            ease_factor_at_review=ease_factor_before_review
        )
        return self

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
