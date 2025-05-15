from rest_framework import serializers
from .models import Sentence, Review


class SentenceSerializer(serializers.ModelSerializer):
    average_score = serializers.SerializerMethodField()
    last_reviewed_date = serializers.SerializerMethodField()

    class Meta:
        model = Sentence
        fields = [ # Specify fields to include in the API response
            'sentence_id',
            'csv_number',
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

    class Meta(SentenceSerializer.Meta): # Inherit Meta to keep model and base fields
        fields = SentenceSerializer.Meta.fields + ['reviews'] 