from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta
from django.db.models import Sum

from .models import Sentence, Review, GRADUATING_INTERVAL_DAYS
from .serializers import SentenceSerializer, ReviewInputSerializer, StatisticsSerializer

from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination


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


class StatisticsAPIView(APIView):
    """
    API endpoint to retrieve learning statistics.
    """
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday()) # Monday of the current week

        # Reviews today
        reviews_today_qs = Review.objects.filter(review_timestamp__date=today)
        reviews_today_count = reviews_today_qs.count()
        new_cards_reviewed_today_count = reviews_today_qs.filter(interval_at_review=0).count()

        # Reviews this week
        reviews_this_week_count = Review.objects.filter(review_timestamp__date__gte=start_of_week).count()
        
        # Total reviews all time
        total_reviews_all_time_count = Review.objects.count()

        # Sentences statistics
        total_sentences_count = Sentence.objects.count()
        
        sentences_learned_count = Sentence.objects.filter(total_reviews__gt=0).count()
        
        # Mastered sentences: is_learning=False, interval >= graduating_interval, consecutive_correct >= 3 (as per PRD)
        # Using a slightly simplified check: is_learning=False and interval_days >= GRADUATING_INTERVAL_DAYS is a strong indicator
        # The PRD also mentions score > 0.8 for last 3-5 reviews, which `consecutive_correct_reviews` partially captures.
        sentences_mastered_count = Sentence.objects.filter(
            is_learning=False, 
            interval_days__gte=GRADUATING_INTERVAL_DAYS, 
            consecutive_correct_reviews__gte=3 # Added this for stricter mastery
        ).count()

        # Overall average score
        # Sum of (average_score_for_sentence * number_of_reviews_for_sentence) / total_number_of_all_reviews
        # Or, sum of all user_score in Review table / total number of reviews
        # The latter is simpler and more direct if Review table is the source of truth for scores.
        # Let's use the sum of all review scores / total reviews for now.
        overall_average_score = None
        if total_reviews_all_time_count > 0:
            total_score_sum_from_reviews = Review.objects.aggregate(total_score=Sum('user_score'))['total_score']
            if total_score_sum_from_reviews is not None:
                overall_average_score = round(total_score_sum_from_reviews / total_reviews_all_time_count, 4)

        percentage_learned_val = None
        if total_sentences_count > 0:
            percentage_learned_val = round((sentences_learned_count / total_sentences_count) * 100.0, 2)
        
        stats_data = {
            "reviews_today": reviews_today_count,
            "new_cards_reviewed_today": new_cards_reviewed_today_count,
            "reviews_this_week": reviews_this_week_count,
            "total_reviews_all_time": total_reviews_all_time_count,
            "overall_average_score": overall_average_score,
            "total_sentences": total_sentences_count,
            "sentences_mastered": sentences_mastered_count,
            "sentences_learned": sentences_learned_count,
            "percentage_learned": percentage_learned_val
        }

        serializer = StatisticsSerializer(data=stats_data)
        if serializer.is_valid(): # This will also ensure all fields are present
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # This case should ideally not be reached if data is prepared correctly
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25 # Default page size
    page_size_query_param = 'page_size'
    max_page_size = 100


class SentenceListAPIView(ListAPIView):
    """
    API endpoint to list all sentences with key statistics.
    Supports pagination.
    """
    queryset = Sentence.objects.all().order_by('csv_number') # Default ordering
    serializer_class = SentenceSerializer
    pagination_class = StandardResultsSetPagination

    # Future considerations for filtering/sorting:
    # filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # filterset_fields = ['is_learning', 'key_spanish_word'] # Example filter fields
    # ordering_fields = ['csv_number', 'next_review_date', 'total_reviews'] # Example ordering fields
    # For ordering by calculated/annotated fields like average_score or last_reviewed_date,
    # we would need to implement queryset annotations and add them to ordering_fields.
