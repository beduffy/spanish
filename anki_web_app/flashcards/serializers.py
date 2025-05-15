from rest_framework import serializers
from .models import Sentence


class SentenceSerializer(serializers.ModelSerializer):
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
            # Add other fields the frontend might need for display or context
            # For now, keeping it to essential card data and SRS status indicators.
        ]
        # Example of read_only_fields if we were doing POST/PUT, not relevant for GET-only next-card
        # read_only_fields = ['sentence_id', 'csv_number', 'creation_date'] 


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