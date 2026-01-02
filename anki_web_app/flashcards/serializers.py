from rest_framework import serializers
from .models import Sentence, Review, Card, CardReview, Lesson, Token, Phrase


class SentenceSerializer(serializers.ModelSerializer):
    average_score = serializers.SerializerMethodField()
    last_reviewed_date = serializers.SerializerMethodField()

    class Meta:
        model = Sentence
        fields = [ # Specify fields to include in the API response
            'sentence_id',
            'csv_number',
            'translation_direction', # Added for bidirectional cards
            'key_spanish_word',
            'key_word_english_translation',
            'spanish_sentence_example',
            'english_sentence_example',
            'base_comment',
            'ai_explanation',
            'next_review_date',
            'is_learning',
            'interval_days', # Added for more context in list view
            'total_reviews', # Added for list view context
            'average_score',
            'last_reviewed_date',
            'ease_factor',
            'creation_date',
            'last_modified_date',
            'total_score_sum',
            'consecutive_correct_reviews',
            # Add other fields the frontend might need for display or context
            # For now, keeping it to essential card data and SRS status indicators.
        ]
        # Example of read_only_fields if we were doing POST/PUT, not relevant for GET-only next-card
        # read_only_fields = ['sentence_id', 'csv_number', 'creation_date'] 

    def get_average_score(self, obj):
        if obj.total_reviews > 0 and obj.total_score_sum is not None:
            return round(obj.total_score_sum / obj.total_reviews, 2)
        return None

    def get_last_reviewed_date(self, obj):
        last_review = obj.reviews.order_by('-review_timestamp').first()
        if last_review:
            return last_review.review_timestamp
        return None


class ReviewInputSerializer(serializers.Serializer):
    sentence_id = serializers.IntegerField()
    user_score = serializers.FloatField(min_value=0.0, max_value=1.0)
    user_comment_addon = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def create(self, validated_data):
        # This serializer is for input validation, not for creating an object directly
        raise NotImplementedError()

    def update(self, instance, validated_data):
        # This serializer is for input validation, not for updating an object directly
        raise NotImplementedError()


class StatisticsSerializer(serializers.Serializer):
    reviews_today = serializers.IntegerField()
    new_cards_reviewed_today = serializers.IntegerField()
    reviews_this_week = serializers.IntegerField()
    total_reviews_all_time = serializers.IntegerField()
    overall_average_score = serializers.FloatField(allow_null=True) # Allow null if no reviews yet
    total_sentences = serializers.IntegerField()
    sentences_mastered = serializers.IntegerField()
    sentences_learned = serializers.IntegerField() # Unique sentences with at least one review
    percentage_learned = serializers.FloatField(allow_null=True) # Allow null if total_sentences is 0

    def create(self, validated_data):
        raise NotImplementedError("This serializer is for output only.")

    def update(self, instance, validated_data):
        raise NotImplementedError("This serializer is for output only.")


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'review_id',
            'review_timestamp',
            'user_score',
            'user_comment_addon',
            'interval_at_review',
            'ease_factor_at_review'
        ]


class SentenceDetailSerializer(SentenceSerializer): # Inherits from SentenceSerializer
    reviews = ReviewSerializer(many=True, read_only=True) # Nested list of reviews

    # Meta inheritance is handled by SentenceSerializer, so no need to redefine fields here explicitly
    # unless we are adding fields specific only to Detail, which 'reviews' is.
    # The base fields including 'translation_direction' will be inherited.
    class Meta(SentenceSerializer.Meta): # Inherit Meta to keep model and base fields
        # Ensure 'reviews' is added to the inherited list of fields
        fields = list(SentenceSerializer.Meta.fields) + ['reviews'] 


class CardReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardReview
        fields = [
            'review_id',
            'review_timestamp',
            'user_score',
            'user_comment_addon',
            'typed_input',
            'interval_at_review',
            'ease_factor_at_review'
        ]


class CardSerializer(serializers.ModelSerializer):
    average_score = serializers.SerializerMethodField()
    last_reviewed_date = serializers.SerializerMethodField()
    mastery_level = serializers.SerializerMethodField()
    linked_card = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    class Meta:
        model = Card
        fields = [
            'card_id',
            'pair_id',
            'linked_card',
            'front',
            'back',
            'language',
            'tags',
            'notes',
            'source',
            'next_review_date',
            'is_learning',
            'interval_days',
            'total_reviews',
            'average_score',
            'last_reviewed_date',
            'ease_factor',
            'creation_date',
            'last_modified_date',
            'total_score_sum',
            'consecutive_correct_reviews',
            'mastery_level',
        ]
        read_only_fields = ['card_id', 'pair_id', 'next_review_date', 'is_learning', 
                           'interval_days', 'total_reviews', 'ease_factor', 'creation_date', 
                           'last_modified_date', 'total_score_sum', 'consecutive_correct_reviews']

    def to_internal_value(self, data):
        # Filter out readonly fields before validation
        readonly = set(self.Meta.read_only_fields)
        filtered_data = {k: v for k, v in data.items() if k not in readonly}
        return super().to_internal_value(filtered_data)

    def get_average_score(self, obj):
        if obj.total_reviews > 0 and obj.total_score_sum is not None:
            return round(obj.total_score_sum / obj.total_reviews, 2)
        return None

    def get_last_reviewed_date(self, obj):
        last_review = obj.reviews.order_by('-review_timestamp').first()
        if last_review:
            return last_review.review_timestamp
        return None

    def get_mastery_level(self, obj):
        """
        Calculate mastery level based on reviews and performance.
        Returns a dict with level name, score, and indicators.
        """
        from .models import GRADUATING_INTERVAL_DAYS
        
        if obj.total_reviews == 0:
            return {
                'level': 'New',
                'score': None,
                'color': 'gray'
            }
        
        # Calculate average score manually since it's a SerializerMethodField
        avg_score = None
        if obj.total_reviews > 0 and obj.total_score_sum is not None:
            avg_score = round(obj.total_score_sum / obj.total_reviews, 2)
        
        # Mastered: graduated, high consecutive correct, long interval
        if not obj.is_learning and obj.consecutive_correct_reviews >= 3 and obj.interval_days >= GRADUATING_INTERVAL_DAYS:
            return {
                'level': 'Mastered',
                'score': avg_score,
                'color': 'green',
                'indicator': f'{obj.consecutive_correct_reviews} consecutive, {obj.interval_days}d interval'
            }
        
        # Excellent: high average score, multiple reviews
        if avg_score and avg_score >= 0.9 and obj.total_reviews >= 5:
            return {
                'level': 'Excellent',
                'score': avg_score,
                'color': 'blue',
                'indicator': f'{obj.total_reviews} reviews'
            }
        
        # Good: decent average score
        if avg_score and avg_score >= 0.8 and obj.total_reviews >= 3:
            return {
                'level': 'Good',
                'score': avg_score,
                'color': 'cyan',
                'indicator': f'{obj.total_reviews} reviews'
            }
        
        # Learning: in learning phase or low reviews
        if obj.is_learning or obj.total_reviews < 3:
            return {
                'level': 'Learning',
                'score': avg_score,
                'color': 'yellow',
                'indicator': f'{obj.total_reviews} reviews'
            }
        
        # Default: needs improvement
        return {
            'level': 'Needs Practice',
            'score': avg_score,
            'color': 'orange',
            'indicator': f'{obj.total_reviews} reviews'
        }


class CardCreateSerializer(serializers.ModelSerializer):
    create_reverse = serializers.BooleanField(default=True, help_text="Auto-create reverse card and link the pair")

    class Meta:
        model = Card
        fields = [
            'front',
            'back',
            'language',
            'tags',
            'notes',
            'source',
            'create_reverse',
        ]

    def validate(self, attrs):
        front = (attrs.get('front') or '').strip()
        back = (attrs.get('back') or '').strip()
        if not front:
            raise serializers.ValidationError({"front": "Front cannot be empty."})
        if not back:
            raise serializers.ValidationError({"back": "Back cannot be empty."})
        return attrs

    def create(self, validated_data):
        create_reverse = validated_data.pop('create_reverse', True)
        
        # User is already set by perform_create in the view
        user = validated_data.get('user')
        
        # Ensure new cards are due today (available for review immediately)
        from django.utils import timezone
        if 'next_review_date' not in validated_data:
            validated_data['next_review_date'] = timezone.now().date()
        
        forward = Card.objects.create(**validated_data)

        if not create_reverse:
            return forward

        reverse = Card.objects.create(
            pair_id=forward.pair_id,
            front=forward.back,
            back=forward.front,
            language=forward.language or '',  # Copy language if set, default to empty string
            tags=forward.tags,
            notes=forward.notes,
            source=forward.source or '',  # Copy source if set, default to empty string
            user=user,
            next_review_date=timezone.now().date(),  # Ensure reverse card is also due today
        )

        forward.linked_card = reverse
        reverse.linked_card = forward
        forward.save(update_fields=['linked_card'])
        reverse.save(update_fields=['linked_card'])

        # Refresh from database to ensure all relationships are properly loaded
        forward.refresh_from_db()
        
        return forward

    def to_representation(self, instance):
        """
        Use CardSerializer for the response to ensure proper serialization
        of all fields including linked_card (as ID only).
        """
        # Create a new CardSerializer instance to avoid any potential recursion
        # Pass context if available to maintain request context
        context = getattr(self, '_context', {})
        serializer = CardSerializer(instance, context=context)
        return serializer.data


class CardDetailSerializer(CardSerializer):
    reviews = CardReviewSerializer(many=True, read_only=True)

    class Meta(CardSerializer.Meta):
        fields = list(CardSerializer.Meta.fields) + ['reviews']


class CardReviewInputSerializer(serializers.Serializer):
    card_id = serializers.IntegerField()
    user_score = serializers.FloatField(min_value=0.0, max_value=1.0)
    user_comment_addon = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    typed_input = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def create(self, validated_data):
        raise NotImplementedError()

    def update(self, instance, validated_data):
        raise NotImplementedError()


class LessonSerializer(serializers.ModelSerializer):
    token_count = serializers.SerializerMethodField()
    listening_time_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'lesson_id', 'title', 'text', 'language', 'audio_url',
            'source_type', 'source_url', 'created_at', 'token_count',
            'total_listening_time_seconds', 'last_listened_at', 'listening_time_formatted'
        ]
        read_only_fields = ['lesson_id', 'created_at', 'total_listening_time_seconds', 'last_listened_at']
    
    def get_token_count(self, obj):
        return obj.tokens.count()
    
    def get_listening_time_formatted(self, obj):
        """Format listening time as MM:SS or HH:MM:SS."""
        seconds = obj.total_listening_time_seconds or 0
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = [
            'token_id', 'text', 'normalized', 'start_offset', 'end_offset',
            'translation', 'clicked_count', 'added_to_flashcards', 'card_id'
        ]
        read_only_fields = ['token_id', 'clicked_count', 'added_to_flashcards', 'card_id']


class LessonDetailSerializer(LessonSerializer):
    tokens = TokenSerializer(many=True, read_only=True)
    
    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + ['tokens']


class LessonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['title', 'text', 'language', 'audio_url', 'source_type', 'source_url']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        lesson = Lesson.objects.create(**validated_data)
        
        # Tokenize the text
        token_count = 0
        try:
            from .tokenization import tokenize_text
            tokens_data = tokenize_text(lesson.text)
            
            if not tokens_data:
                print(f"[LessonCreateSerializer] Warning: No tokens generated for lesson {lesson.lesson_id}")
            else:
                print(f"[LessonCreateSerializer] Generated {len(tokens_data)} tokens for lesson {lesson.lesson_id}")
            
            for token_data in tokens_data:
                try:
                    # Remove 'type' field as Token model doesn't have it
                    token_data_clean = {k: v for k, v in token_data.items() if k != 'type'}
                    Token.objects.create(
                        lesson=lesson,
                        **token_data_clean
                    )
                    token_count += 1
                except Exception as e:
                    print(f"[LessonCreateSerializer] Error creating token: {e}")
                    print(f"[LessonCreateSerializer] Token data: {token_data}")
                    import traceback
                    traceback.print_exc()
                    # Continue with other tokens even if one fails
                    continue
        except Exception as e:
            print(f"[LessonCreateSerializer] Error during tokenization: {e}")
            import traceback
            traceback.print_exc()
            # Still return the lesson even if tokenization fails
        
        # Refresh lesson to get updated token count
        lesson.refresh_from_db()
        return lesson
    
    def to_representation(self, instance):
        """Add token_count to the response"""
        data = super().to_representation(instance)
        data['token_count'] = instance.tokens.count()
        return data


class TranslateRequestSerializer(serializers.Serializer):
    text = serializers.CharField()
    source_lang = serializers.CharField(default='es')
    target_lang = serializers.CharField(default='en')


class AddToFlashcardsSerializer(serializers.Serializer):
    token_id = serializers.IntegerField(required=False)
    phrase_id = serializers.IntegerField(required=False)
    front = serializers.CharField()  # Word/phrase in source language
    back = serializers.CharField()  # Translation
    sentence_context = serializers.CharField(required=False, allow_blank=True)
    lesson_id = serializers.IntegerField()
    
    def validate(self, attrs):
        if not attrs.get('token_id') and not attrs.get('phrase_id'):
            raise serializers.ValidationError("Either token_id or phrase_id required")
        return attrs