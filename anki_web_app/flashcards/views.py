from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Sentence
from .serializers import SentenceSerializer, ReviewInputSerializer


class NextCardAPIView(APIView):
    """
    API endpoint to get the next flashcard for review.

    Prioritizes cards due for review (next_review_date <= today),
    then new cards (interval_days == 0 and next_review_date <= today).
    """
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        next_card = None

        # 1. Check for review cards due today or earlier
        review_cards_due = Sentence.objects.filter(
            next_review_date__lte=today,
            is_learning=False
        ).order_by('next_review_date', 'csv_number') # Oldest review date first, then by CSV number
        
        if review_cards_due.exists():
            next_card = review_cards_due.first()
        else:
            # 2. If no review cards, check for new cards (is_learning=True, interval_days=0)
            #    OR cards in learning phase that are due today (e.g. step 1 of learning)
            learning_or_new_cards_due = Sentence.objects.filter(
                next_review_date__lte=today,
                is_learning=True # Includes both truly new (interval_days=0) and learning step cards
            ).order_by('next_review_date', 'csv_number') # Prioritize by due date, then by CSV number for new cards

            if learning_or_new_cards_due.exists():
                next_card = learning_or_new_cards_due.first()

        if next_card:
            serializer = SentenceSerializer(next_card)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # No cards due for review and no new cards available
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubmitReviewAPIView(APIView):
    """
    API endpoint to submit a review for a sentence.
    Accepts sentence_id, user_score, and an optional user_comment_addon.
    Updates SRS parameters and appends comment to the sentence's base_comment.
    """
    def post(self, request, *args, **kwargs):
        serializer = ReviewInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        sentence_id = validated_data.get('sentence_id')
        user_score = validated_data.get('user_score')
        user_comment_addon = validated_data.get('user_comment_addon')

        try:
            sentence = Sentence.objects.get(pk=sentence_id)
        except Sentence.DoesNotExist:
            return Response({"error": "Sentence not found."}, status=status.HTTP_404_NOT_FOUND)

        # Process the review using the model method (updates SRS, creates Review object)
        sentence.process_review(user_score, user_comment_addon)

        # Append comment to base_comment with timestamp if a comment was provided
        if user_comment_addon and user_comment_addon.strip():
            timestamp = timezone.now().strftime("%H:%M %b %d, %Y") # e.g., 15:31 May 15, 2023
            new_comment_line = f"\n{timestamp}: {user_comment_addon.strip()}"
            
            if sentence.base_comment and sentence.base_comment.strip():
                sentence.base_comment += new_comment_line
            else:
                sentence.base_comment = new_comment_line.lstrip() # Avoid leading newline if base_comment was empty
            sentence.save() # Save after updating base_comment

        # Return the updated sentence data
        response_serializer = SentenceSerializer(sentence)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
