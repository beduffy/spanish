from django.db import models
from django.utils import timezone
from datetime import timedelta # Ensure timedelta is imported
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

# Constants for SRS logic
INITIAL_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3
GRADUATING_INTERVAL_DAYS = 4 # First interval after graduating from learning steps
LAPSE_INTERVAL_DAYS = 0 # Interval when a review card lapses (back to learning step 1)
LEARNING_STEPS_DAYS = [1, 3] # Intervals for learning steps: 1 day, then 3 days

class Sentence(models.Model):
    TRANSLATION_DIRECTIONS = [
        ('S2E', 'Spanish to English'),
        ('E2S', 'English to Spanish'),
    ]

    sentence_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sentences', help_text="User who owns this sentence card")
    # csv_number will be unique in combination with translation_direction
    csv_number = models.IntegerField(help_text="Original number from CSV for reference")
    translation_direction = models.CharField(
        max_length=3,
        choices=TRANSLATION_DIRECTIONS,
        default='S2E',
        help_text="Direction of translation for this card (e.g., Spanish to English)"
    )
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
        return f"{self.csv_number} ({self.get_translation_direction_display()}): {self.key_spanish_word} - {self.spanish_sentence_example[:50]}..."

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
        ordering = ['csv_number', 'translation_direction']
        unique_together = [['csv_number', 'translation_direction']]
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


class Card(models.Model):
    """
    General two-sided card (front/back) with SRS fields.

    Note: For now this exists alongside the legacy Sentence model so we can migrate incrementally.
    """

    card_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cards', help_text="User who owns this card")

    pair_id = models.UUIDField(default=uuid.uuid4, db_index=True, help_text="Shared ID for a forward+reverse pair")
    linked_card = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_card_reverse',
        help_text="The reverse card for this card (if any)."
    )

    front = models.TextField(help_text="Prompt (front of card)")
    back = models.TextField(help_text="Answer (back of card)")

    language = models.CharField(max_length=32, blank=True, default="", help_text="Optional language label (e.g., 'es', 'de')")
    tags = models.JSONField(default=list, blank=True, help_text="Optional list of tags")
    notes = models.TextField(blank=True, default="", help_text="Optional notes")
    source = models.TextField(blank=True, default="", help_text="Optional source")

    creation_date = models.DateTimeField(default=timezone.now, help_text="Timestamp of creation")
    last_modified_date = models.DateTimeField(auto_now=True, help_text="Timestamp of last update to card or SRS data")

    ease_factor = models.FloatField(default=INITIAL_EASE_FACTOR, help_text="For SM2-like algorithm")
    interval_days = models.IntegerField(default=0, help_text="Current interval in days; 0 for new/learning cards")
    next_review_date = models.DateField(default=timezone.now, help_text="Date for next scheduled review")
    is_learning = models.BooleanField(default=True, help_text="True if card is in learning phase, False if graduated/reviewing")
    consecutive_correct_reviews = models.IntegerField(default=0, help_text="Number of consecutive reviews with score > 0.8")
    total_reviews = models.IntegerField(default=0, help_text="Counter for how many times this card has been reviewed")
    total_score_sum = models.FloatField(default=0.0, help_text="Sum of all scores for this card, to calculate average")

    def __str__(self):
        return f"Card {self.card_id}: {self.front[:50]}..."

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

    def process_review(self, user_score, review_comment=None, typed_input=None, session=None):
        # Store current state for the Review object
        interval_before_review = self.interval_days
        ease_factor_before_review = self.ease_factor

        q = self._get_quality_from_score(user_score)

        # Update consecutive_correct_reviews (for mastery definition: score > 0.8)
        if user_score > 0.8:  # Corresponds to q >= 4
            self.consecutive_correct_reviews += 1
        else:
            self.consecutive_correct_reviews = 0

        if self.is_learning:
            if q >= 3:  # Passed a learning step
                current_step_index = -1
                if self.interval_days == 0:  # Just starting or failed previous step
                    current_step_index = -1  # Will move to LEARNING_STEPS_DAYS[0]
                elif self.interval_days == LEARNING_STEPS_DAYS[0]:
                    current_step_index = 0
                elif self.interval_days == LEARNING_STEPS_DAYS[1]:
                    current_step_index = 1

                next_step_index = current_step_index + 1
                if next_step_index < len(LEARNING_STEPS_DAYS):
                    self.interval_days = LEARNING_STEPS_DAYS[next_step_index]
                else:  # Graduated from learning steps
                    self.is_learning = False
                    self.interval_days = GRADUATING_INTERVAL_DAYS
            else:  # Failed a learning step
                self.interval_days = 0  # Reset to the first learning step (due now or next day)
        else:  # Reviewing a graduated card
            if q >= 3:  # Correct recall
                if self.interval_days == 0:  # Safeguard
                    self.interval_days = GRADUATING_INTERVAL_DAYS
                else:
                    self.interval_days = round(self.interval_days * self.ease_factor)
            else:  # Incorrect recall (Lapse)
                self.is_learning = True
                self.interval_days = LAPSE_INTERVAL_DAYS  # Reset to first learning step
                self.ease_factor = max(MIN_EASE_FACTOR, self.ease_factor - 0.20)  # Penalize EF

        # Update Ease Factor if quality was good enough (q >= 3)
        if q >= 3:
            new_ef = self.ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
            self.ease_factor = max(MIN_EASE_FACTOR, new_ef)

        self.next_review_date = timezone.now().date() + timedelta(days=self.interval_days)

        # Update totals
        self.total_reviews += 1
        self.total_score_sum += user_score

        self.save()

        CardReview.objects.create(
            card=self,
            session=session,
            user_score=user_score,
            user_comment_addon=review_comment,
            typed_input=typed_input,
            interval_at_review=interval_before_review,
            ease_factor_at_review=ease_factor_before_review
        )
        return self

    class Meta:
        ordering = ['-next_review_date', 'card_id']
        verbose_name = "Card"
        verbose_name_plural = "Cards"


class CardReview(models.Model):
    review_id = models.AutoField(primary_key=True)
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='reviews')
    session = models.ForeignKey('StudySession', on_delete=models.SET_NULL, null=True, blank=True, related_name='card_reviews', help_text="Study session this review belongs to")
    review_timestamp = models.DateTimeField(default=timezone.now, help_text="Timestamp of the review")
    user_score = models.FloatField(help_text="Score given by user, 0.0 to 1.0")
    user_comment_addon = models.TextField(blank=True, null=True, help_text="Additional comment made by user during this specific review")
    typed_input = models.TextField(blank=True, null=True, help_text="Optional typed input stored with the review (not graded yet)")
    interval_at_review = models.IntegerField(help_text="The interval setting for the card before this review took place")
    ease_factor_at_review = models.FloatField(help_text="The ease factor for the card before this review took place")

    def __str__(self):
        return f"Review for card {self.card.card_id} at {self.review_timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-review_timestamp']
        verbose_name = "Card Review"
        verbose_name_plural = "Card Reviews"


class StudySession(models.Model):
    """
    Tracks study sessions with activity timestamps for AFK detection.
    Active minutes are calculated by ignoring gaps > AFK_THRESHOLD_SECONDS.
    """
    AFK_THRESHOLD_SECONDS = 90  # Default: 90 seconds

    session_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_sessions', help_text="User who owns this session")
    start_time = models.DateTimeField(default=timezone.now, help_text="When the session started")
    end_time = models.DateTimeField(null=True, blank=True, help_text="When the session ended (null if active)")
    last_activity_time = models.DateTimeField(default=timezone.now, help_text="Last recorded activity timestamp")
    is_active = models.BooleanField(default=True, help_text="True if session is still active")

    def __str__(self):
        status = "active" if self.is_active else "ended"
        return f"Session {self.session_id} ({status}) - User: {self.user.username}"

    def record_activity(self):
        """Record a heartbeat/activity ping."""
        if self.is_active:
            self.last_activity_time = timezone.now()
            self.save(update_fields=['last_activity_time'])

    def end_session(self):
        """End the session."""
        if self.is_active:
            self.end_time = timezone.now()
            self.is_active = False
            self.save(update_fields=['end_time', 'is_active'])

    def calculate_active_minutes(self, afk_threshold_seconds=None):
        """
        Calculate active minutes by ignoring gaps > afk_threshold_seconds.
        Returns the total active time in minutes (float).
        """
        if afk_threshold_seconds is None:
            afk_threshold_seconds = self.AFK_THRESHOLD_SECONDS

        # Get all activity events (heartbeats) for this session
        activities = list(self.session_activities.order_by('timestamp'))
        
        if not activities:
            # No activities recorded, use start -> end (or now if active)
            end = self.end_time or timezone.now()
            total_seconds = (end - self.start_time).total_seconds()
            return max(0, total_seconds / 60.0)

        # Start with session start time
        total_active_seconds = 0
        last_activity = self.start_time

        for activity in activities:
            gap_seconds = (activity.timestamp - last_activity).total_seconds()
            if gap_seconds <= afk_threshold_seconds:
                # Active period - add to total
                total_active_seconds += gap_seconds
            # else: gap > threshold, treat as AFK, don't add to active time
            last_activity = activity.timestamp

        # Add time from last activity to end (or now if active)
        end = self.end_time or timezone.now()
        final_gap_seconds = (end - last_activity).total_seconds()
        if final_gap_seconds <= afk_threshold_seconds:
            total_active_seconds += final_gap_seconds

        return total_active_seconds / 60.0  # Convert to minutes

    class Meta:
        ordering = ['-start_time']
        verbose_name = "Study Session"
        verbose_name_plural = "Study Sessions"


class SessionActivity(models.Model):
    """
    Individual activity/heartbeat events within a study session.
    Used to calculate active minutes with AFK threshold.
    """
    activity_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='session_activities', help_text="The study session this activity belongs to")
    timestamp = models.DateTimeField(default=timezone.now, help_text="When this activity occurred")

    def __str__(self):
        return f"Activity {self.activity_id} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['timestamp']
        verbose_name = "Session Activity"
        verbose_name_plural = "Session Activities"


class Lesson(models.Model):
    """
    Represents an imported text/audio lesson (like a LingQ lesson).
    """
    lesson_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lessons')
    
    title = models.CharField(max_length=500)
    text = models.TextField(help_text="Full text content")
    language = models.CharField(max_length=10, default='de', help_text="Language code (de, es, etc.)")
    
    # Audio support
    audio_url = models.URLField(blank=True, null=True, help_text="URL to audio file")
    audio_file = models.FileField(upload_to='lessons/audio/', blank=True, null=True)
    
    # Source tracking
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('text', 'Text Paste'),
            ('youtube', 'YouTube'),
            ('url', 'URL'),
            ('file', 'File Upload'),
        ],
        default='text'
    )
    source_url = models.URLField(blank=True, null=True, help_text="Original source URL")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Translation cache (sentence-level)
    sentence_translations = models.JSONField(
        default=dict,
        blank=True,
        help_text="Cached translations: {sentence_text: translation}"
    )
    
    # Listening time tracking
    total_listening_time_seconds = models.IntegerField(default=0, help_text="Total seconds of audio listened")
    last_listened_at = models.DateTimeField(blank=True, null=True, help_text="Last time audio was played")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"


class Token(models.Model):
    """
    Represents a word/phrase token within a lesson.
    Used for highlighting and click-to-translate.
    """
    token_id = models.AutoField(primary_key=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='tokens')
    
    # Token text and position
    text = models.CharField(max_length=200, help_text="Surface form of the token")
    normalized = models.CharField(max_length=200, db_index=True, help_text="Normalized form (lowercase, punctuation stripped)")
    
    # Position in lesson text
    start_offset = models.IntegerField(help_text="Character offset where token starts")
    end_offset = models.IntegerField(help_text="Character offset where token ends")
    
    # Translation cache (word-level)
    translation = models.TextField(blank=True, null=True, help_text="Cached translation/gloss")
    dictionary_entry = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dictionary data: {meanings: [...], part_of_speech: '...'}"
    )
    
    # User interaction tracking
    clicked_count = models.IntegerField(default=0, help_text="How many times user clicked this token")
    added_to_flashcards = models.BooleanField(default=False, help_text="Whether user added this to flashcards")
    card_id = models.IntegerField(blank=True, null=True, help_text="ID of Card created from this token")
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['start_offset']
        indexes = [
            models.Index(fields=['lesson', 'start_offset']),
            models.Index(fields=['normalized']),
        ]
        verbose_name = "Token"
        verbose_name_plural = "Tokens"


class Phrase(models.Model):
    """
    Represents a multi-word phrase selected by the user.
    """
    phrase_id = models.AutoField(primary_key=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='phrases')
    
    text = models.TextField(help_text="Full phrase text")
    normalized = models.CharField(max_length=500, db_index=True)
    
    # Token references (which tokens make up this phrase)
    token_start = models.ForeignKey(
        Token,
        on_delete=models.CASCADE,
        related_name='phrase_starts',
        help_text="First token in phrase"
    )
    token_end = models.ForeignKey(
        Token,
        on_delete=models.CASCADE,
        related_name='phrase_ends',
        help_text="Last token in phrase"
    )
    
    translation = models.TextField(blank=True, null=True)
    added_to_flashcards = models.BooleanField(default=False)
    card_id = models.IntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Phrase"
        verbose_name_plural = "Phrases"
