from rest_framework import serializers
from .models import Sentence, Review, Card, CardReview


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
        ]
        read_only_fields = ['card_id', 'pair_id', 'linked_card', 'next_review_date', 'is_learning', 
                           'interval_days', 'total_reviews', 'ease_factor', 'creation_date', 
                           'last_modified_date', 'total_score_sum', 'consecutive_correct_reviews']

    def get_average_score(self, obj):
        if obj.total_reviews > 0 and obj.total_score_sum is not None:
            return round(obj.total_score_sum / obj.total_reviews, 2)
        return None

    def get_last_reviewed_date(self, obj):
        last_review = obj.reviews.order_by('-review_timestamp').first()
        if last_review:
            return last_review.review_timestamp
        return None


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
        
        # Assign user from request if authenticated
        user = None
        if self.context.get('request') and self.context['request'].user.is_authenticated:
            user = self.context['request'].user
        
        validated_data['user'] = user
        forward = Card.objects.create(**validated_data)

        if not create_reverse:
            return forward

        reverse = Card.objects.create(
            pair_id=forward.pair_id,
            front=forward.back,
            back=forward.front,
            language=forward.language,
            tags=forward.tags,
            notes=forward.notes,
            source=forward.source,
            user=user,
        )

        forward.linked_card = reverse
        reverse.linked_card = forward
        forward.save(update_fields=['linked_card'])
        reverse.save(update_fields=['linked_card'])

        return forward


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