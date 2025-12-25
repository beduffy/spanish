from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta
from django.db.models import Sum
import csv
import io
import uuid

from .models import Sentence, Review, GRADUATING_INTERVAL_DAYS, Card, CardReview
from .serializers import (
    SentenceSerializer,
    ReviewInputSerializer,
    StatisticsSerializer,
    SentenceDetailSerializer,
    CardSerializer,
    CardCreateSerializer,
    CardDetailSerializer,
    CardReviewInputSerializer,
)

from rest_framework.generics import ListAPIView, RetrieveAPIView, ListCreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated


class UserScopedMixin:
    """
    Mixin to scope querysets by authenticated user.
    Falls back to all objects if user is anonymous (for backward compatibility during migration).
    """
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user and self.request.user.is_authenticated:
            # Filter by user if authenticated
            if hasattr(queryset.model, 'user'):
                return queryset.filter(user=self.request.user)
        # For backward compatibility: if no user or anonymous, return all (during migration period)
        # TODO: Remove this fallback once all data is migrated and users are required
        return queryset


class NextCardAPIView(APIView):
    """
    API endpoint to get the next flashcard for review.

    Prioritizes cards due for review (next_review_date <= today),
    then new cards (interval_days == 0 and next_review_date <= today).
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        next_card = None
        
        # Scope by user if authenticated
        base_queryset = Sentence.objects.all()
        if request.user and request.user.is_authenticated:
            base_queryset = base_queryset.filter(user=request.user)

        # 1. Check for review cards due today or earlier
        review_cards_due = base_queryset.filter(
            next_review_date__lte=today,
            is_learning=False
        ).order_by('next_review_date', 'csv_number') # Oldest review date first, then by CSV number
        
        if review_cards_due.exists():
            next_card = review_cards_due.first()
        else:
            # 2. If no review cards, check for new cards (is_learning=True, interval_days=0)
            #    OR cards in learning phase that are due today (e.g. step 1 of learning)
            learning_or_new_cards_due = base_queryset.filter(
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
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = ReviewInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        sentence_id = validated_data.get('sentence_id')
        user_score = validated_data.get('user_score')
        user_comment_addon = validated_data.get('user_comment_addon')

        try:
            queryset = Sentence.objects.all()
            if request.user and request.user.is_authenticated:
                queryset = queryset.filter(user=request.user)
            sentence = queryset.get(pk=sentence_id)
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
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday()) # Monday of the current week
        
        # Scope by user
        sentence_queryset = Sentence.objects.all()
        review_queryset = Review.objects.all()
        if request.user and request.user.is_authenticated:
            sentence_queryset = sentence_queryset.filter(user=request.user)
            review_queryset = review_queryset.filter(sentence__user=request.user)

        # Reviews today
        reviews_today_qs = review_queryset.filter(review_timestamp__date=today)
        reviews_today_count = reviews_today_qs.count()
        new_cards_reviewed_today_count = reviews_today_qs.filter(interval_at_review=0).count()

        # Reviews this week
        reviews_this_week_count = review_queryset.filter(review_timestamp__date__gte=start_of_week).count()
        
        # Total reviews all time
        total_reviews_all_time_count = review_queryset.count()

        # Sentences statistics
        total_sentences_count = sentence_queryset.count()
        
        sentences_learned_count = sentence_queryset.filter(total_reviews__gt=0).count()
        
        # Mastered sentences: is_learning=False, interval >= graduating_interval, consecutive_correct >= 3 (as per PRD)
        # Using a slightly simplified check: is_learning=False and interval_days >= GRADUATING_INTERVAL_DAYS is a strong indicator
        # The PRD also mentions score > 0.8 for last 3-5 reviews, which `consecutive_correct_reviews` partially captures.
        sentences_mastered_count = sentence_queryset.filter(
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
            total_score_sum_from_reviews = review_queryset.aggregate(total_score=Sum('user_score'))['total_score']
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
    page_size = 100 # Default page size
    page_size_query_param = 'page_size'
    max_page_size = 100


class SentenceListAPIView(UserScopedMixin, ListAPIView):
    """
    API endpoint to list all sentences with key statistics.
    Supports pagination.
    """
    queryset = Sentence.objects.all().order_by('csv_number') # Default ordering
    serializer_class = SentenceSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    # Future considerations for filtering/sorting:
    # filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    # filterset_fields = ['is_learning', 'key_spanish_word'] # Example filter fields
    # ordering_fields = ['csv_number', 'next_review_date', 'total_reviews'] # Example ordering fields
    # For ordering by calculated/annotated fields like average_score or last_reviewed_date,
    # we would need to implement queryset annotations and add them to ordering_fields.


class SentenceDetailAPIView(UserScopedMixin, RetrieveAPIView):
    """
    API endpoint to retrieve details of a single sentence, including its review history.
    """
    queryset = Sentence.objects.all()
    serializer_class = SentenceDetailSerializer
    lookup_field = 'pk' # Corresponds to sentence_id as it's the primary key
    permission_classes = [IsAuthenticated]


class CardListCreateAPIView(UserScopedMixin, ListCreateAPIView):
    """
    Minimal Cards API for v2 migration.

    - GET: list cards
    - POST: create card (auto-creates reverse and links by default)
    """

    queryset = Card.objects.all().order_by('-creation_date', 'card_id')
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CardCreateSerializer
        return CardSerializer


class CardDetailAPIView(UserScopedMixin, RetrieveAPIView):
    queryset = Card.objects.all()
    serializer_class = CardDetailSerializer
    lookup_field = 'pk' # Corresponds to card_id as it's the primary key
    permission_classes = [IsAuthenticated]


class CardNextCardAPIView(APIView):
    """
    Card version of next-card:
    - prioritizes due review cards (is_learning=False)
    - then due learning/new cards (is_learning=True)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        next_card = None
        
        # Scope by user if authenticated
        base_queryset = Card.objects.all()
        if request.user and request.user.is_authenticated:
            base_queryset = base_queryset.filter(user=request.user)

        review_cards_due = base_queryset.filter(
            next_review_date__lte=today,
            is_learning=False
        ).order_by('next_review_date', 'card_id')

        if review_cards_due.exists():
            next_card = review_cards_due.first()
        else:
            learning_or_new_cards_due = base_queryset.filter(
                next_review_date__lte=today,
                is_learning=True
            ).order_by('next_review_date', 'card_id')

            if learning_or_new_cards_due.exists():
                next_card = learning_or_new_cards_due.first()

        if next_card:
            serializer = CardSerializer(next_card)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CardSubmitReviewAPIView(APIView):
    """
    Card version of submit-review.
    Accepts card_id, user_score, optional user_comment_addon, optional typed_input.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CardReviewInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        card_id = validated_data.get('card_id')
        user_score = validated_data.get('user_score')
        user_comment_addon = validated_data.get('user_comment_addon')
        typed_input = validated_data.get('typed_input')

        try:
            queryset = Card.objects.all()
            if request.user and request.user.is_authenticated:
                queryset = queryset.filter(user=request.user)
            card = queryset.get(pk=card_id)
        except Card.DoesNotExist:
            return Response({"error": "Card not found."}, status=status.HTTP_404_NOT_FOUND)

        card.process_review(user_score, user_comment_addon, typed_input)

        response_serializer = CardSerializer(card)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class CardStatisticsAPIView(APIView):
    """
    Basic card statistics (v2) – kept parallel to legacy Sentence stats for now.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        
        # Scope by user
        card_queryset = Card.objects.all()
        review_queryset = CardReview.objects.all()
        if request.user and request.user.is_authenticated:
            card_queryset = card_queryset.filter(user=request.user)
            review_queryset = review_queryset.filter(card__user=request.user)

        reviews_today_qs = review_queryset.filter(review_timestamp__date=today)
        reviews_today_count = reviews_today_qs.count()
        new_cards_reviewed_today_count = reviews_today_qs.filter(interval_at_review=0).count()

        reviews_this_week_count = review_queryset.filter(review_timestamp__date__gte=start_of_week).count()
        total_reviews_all_time_count = review_queryset.count()

        total_cards_count = card_queryset.count()
        cards_learned_count = card_queryset.filter(total_reviews__gt=0).count()

        cards_mastered_count = card_queryset.filter(
            is_learning=False,
            interval_days__gte=GRADUATING_INTERVAL_DAYS,
            consecutive_correct_reviews__gte=3
        ).count()

        overall_average_score = None
        if total_reviews_all_time_count > 0:
            total_score_sum_from_reviews = review_queryset.aggregate(total_score=Sum('user_score'))['total_score']
            if total_score_sum_from_reviews is not None:
                overall_average_score = round(total_score_sum_from_reviews / total_reviews_all_time_count, 4)

        percentage_learned_val = None
        if total_cards_count > 0:
            percentage_learned_val = round((cards_learned_count / total_cards_count) * 100.0, 2)

        stats_data = {
            "reviews_today": reviews_today_count,
            "new_cards_reviewed_today": new_cards_reviewed_today_count,
            "reviews_this_week": reviews_this_week_count,
            "total_reviews_all_time": total_reviews_all_time_count,
            "overall_average_score": overall_average_score,
            "total_cards": total_cards_count,
            "cards_mastered": cards_mastered_count,
            "cards_learned": cards_learned_count,
            "percentage_learned": percentage_learned_val
        }

        return Response(stats_data, status=status.HTTP_200_OK)


class CardUpdateAPIView(UserScopedMixin, UpdateAPIView):
    """
    Update a card (PUT/PATCH).
    """
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]


class CardDeleteAPIView(UserScopedMixin, DestroyAPIView):
    """
    Delete a card (DELETE).
    Also deletes the linked reverse card if it exists.
    """
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        # If this card has a linked reverse card, delete it too
        if instance.linked_card:
            reverse_card = instance.linked_card
            # Unlink first to avoid circular deletion issues
            instance.linked_card = None
            instance.save(update_fields=['linked_card'])
            reverse_card.delete()
        instance.delete()


class CardImportAPIView(APIView):
    """
    Import cards from CSV/TSV file.
    
    Expected POST data:
    - file: uploaded CSV/TSV file
    - front_column: column name/index for front (prompt)
    - back_column: column name/index for back (answer)
    - language: optional language label
    - create_reverse: boolean (default True) - create reverse cards
    - delimiter: optional delimiter (default: auto-detect)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file uploaded."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        front_column = request.data.get('front_column', '')
        back_column = request.data.get('back_column', '')
        language = request.data.get('language', '')
        create_reverse = request.data.get('create_reverse', 'true').lower() == 'true'
        delimiter = request.data.get('delimiter', None)
        preview_only = request.data.get('preview_only', 'false').lower() == 'true'
        
        # Detect delimiter if not provided
        if delimiter is None:
            filename = uploaded_file.name.lower()
            if filename.endswith('.tsv'):
                delimiter = '\t'
            else:
                delimiter = ','
        
        try:
            # Read file content
            file_content = uploaded_file.read().decode('utf-8')
            file_io = io.StringIO(file_content)
            
            # Parse CSV/TSV
            reader = csv.DictReader(file_io, delimiter=delimiter)
            
            if not reader.fieldnames:
                return Response(
                    {"error": "File appears to be empty or invalid."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # If preview only, return columns and sample data
            if preview_only:
                preview_rows = []
                file_io.seek(0)
                reader = csv.DictReader(file_io, delimiter=delimiter)
                for i, row in enumerate(reader):
                    if i >= 5:  # Preview first 5 rows
                        break
                    preview_data = {}
                    if front_column and front_column in row:
                        preview_data['front'] = row.get(front_column, '')
                    if back_column and back_column in row:
                        preview_data['back'] = row.get(back_column, '')
                    if preview_data:
                        preview_rows.append(preview_data)
                
                # Count total rows
                file_io.seek(0)
                total_rows = sum(1 for _ in csv.DictReader(file_io, delimiter=delimiter))
                
                # Reset file_io for reading fieldnames
                file_io.seek(0)
                reader_for_cols = csv.DictReader(file_io, delimiter=delimiter)
                
                return Response({
                    'columns': list(reader_for_cols.fieldnames),
                    'preview': preview_rows if preview_rows else [],
                    'total_rows': total_rows
                }, status=status.HTTP_200_OK)
            
            # For actual import, require front and back columns
            if not front_column or not back_column:
                return Response(
                    {"error": "front_column and back_column are required for import."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate columns exist
            if front_column not in reader.fieldnames:
                return Response(
                    {"error": f"Column '{front_column}' not found in file. Available columns: {', '.join(reader.fieldnames)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if back_column not in reader.fieldnames:
                return Response(
                    {"error": f"Column '{back_column}' not found in file. Available columns: {', '.join(reader.fieldnames)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Actually import the cards
            file_io.seek(0)
            reader = csv.DictReader(file_io, delimiter=delimiter)
            
            created_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):  # start=2 because of header
                try:
                    front = (row.get(front_column) or '').strip()
                    back = (row.get(back_column) or '').strip()
                    
                    if not front or not back:
                        error_count += 1
                        errors.append(f"Row {row_num}: Front or back is empty")
                        continue
                    
                    # Optional fields
                    tags = []
                    if 'tags' in row and row['tags']:
                        # Support both comma and space-separated tags
                        tag_string = row['tags'].strip()
                        if ',' in tag_string:
                            tags = [tag.strip() for tag in tag_string.split(',') if tag.strip()]
                        else:
                            # Space-separated tags
                            tags = [tag.strip() for tag in tag_string.split() if tag.strip()]
                    
                    notes = row.get('notes', '').strip()
                    source = row.get('source', '').strip()
                    
                    # Create forward card
                    forward = Card.objects.create(
                        front=front,
                        back=back,
                        language=language,
                        tags=tags,
                        notes=notes,
                        source=source,
                        user=request.user if request.user.is_authenticated else None,
                    )
                    
                    # Create reverse card if requested
                    if create_reverse:
                        reverse = Card.objects.create(
                            pair_id=forward.pair_id,
                            front=back,
                            back=front,
                            language=language,
                            tags=tags,
                            notes=notes,
                            source=source,
                            user=request.user if request.user.is_authenticated else None,
                        )
                        forward.linked_card = reverse
                        reverse.linked_card = forward
                        forward.save(update_fields=['linked_card'])
                        reverse.save(update_fields=['linked_card'])
                    
                    created_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {row_num}: {str(e)}")
            
            return Response({
                'created_count': created_count,
                'error_count': error_count,
                'errors': errors[:10] if errors else [],  # Limit errors to first 10
            }, status=status.HTTP_201_CREATED)
            
        except UnicodeDecodeError:
            return Response(
                {"error": "File encoding error. Please ensure the file is UTF-8 encoded."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Error processing file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
