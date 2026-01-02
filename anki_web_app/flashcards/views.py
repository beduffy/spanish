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

from .models import Sentence, Review, GRADUATING_INTERVAL_DAYS, Card, CardReview, StudySession, SessionActivity, Lesson, Token, Phrase
from .serializers import (
    SentenceSerializer,
    ReviewInputSerializer,
    StatisticsSerializer,
    SentenceDetailSerializer,
    CardSerializer,
    CardCreateSerializer,
    CardDetailSerializer,
    CardReviewInputSerializer,
    LessonSerializer,
    LessonDetailSerializer,
    LessonCreateSerializer,
    TokenSerializer,
    TranslateRequestSerializer,
    AddToFlashcardsSerializer,
)

from rest_framework.generics import ListAPIView, RetrieveAPIView, ListCreateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

User = get_user_model()


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

    def perform_create(self, serializer):
        """Set the user on the card before creation."""
        serializer.save(user=self.request.user)


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

        # Include cards that are due OR have never been reviewed (total_reviews=0)
        # This ensures newly created cards are immediately available
        from django.db.models import Q
        review_cards_due = base_queryset.filter(
            Q(next_review_date__lte=today) | Q(total_reviews=0),
            is_learning=False
        ).order_by('next_review_date', 'card_id')

        if review_cards_due.exists():
            next_card = review_cards_due.first()
        else:
            learning_or_new_cards_due = base_queryset.filter(
                Q(next_review_date__lte=today) | Q(total_reviews=0),
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
    Accepts card_id, user_score, optional user_comment_addon, optional typed_input, optional session_id.
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
        session_id = request.data.get('session_id')  # Get from request.data, not validated_data

        try:
            queryset = Card.objects.all()
            if request.user and request.user.is_authenticated:
                queryset = queryset.filter(user=request.user)
            card = queryset.get(pk=card_id)
        except Card.DoesNotExist:
            return Response({"error": "Card not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get or create active session if session_id provided
        session = None
        if session_id:
            try:
                session = StudySession.objects.get(
                    session_id=session_id,
                    user=request.user,
                    is_active=True
                )
            except StudySession.DoesNotExist:
                pass  # Session not found or not active, continue without session

        card.process_review(user_score, user_comment_addon, typed_input, session=session)

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


class StudySessionStartAPIView(APIView):
    """
    Start a new study session.
    Returns the session_id for subsequent heartbeat/end calls.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        session = StudySession.objects.create(user=request.user)
        return Response({
            'session_id': session.session_id,
            'start_time': session.start_time,
        }, status=status.HTTP_201_CREATED)


class StudySessionHeartbeatAPIView(APIView):
    """
    Record a heartbeat/activity ping for an active session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = StudySession.objects.get(
                session_id=session_id,
                user=request.user,
                is_active=True
            )
        except StudySession.DoesNotExist:
            return Response({"error": "Active session not found"}, status=status.HTTP_404_NOT_FOUND)

        # Record activity
        session.record_activity()
        SessionActivity.objects.create(session=session)

        return Response({
            'session_id': session.session_id,
            'last_activity_time': session.last_activity_time,
        }, status=status.HTTP_200_OK)


class StudySessionEndAPIView(APIView):
    """
    End an active study session and return active minutes.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            session = StudySession.objects.get(
                session_id=session_id,
                user=request.user,
                is_active=True
            )
        except StudySession.DoesNotExist:
            return Response({"error": "Active session not found"}, status=status.HTTP_404_NOT_FOUND)

        # End the session
        session.end_session()
        active_minutes = session.calculate_active_minutes()

        return Response({
            'session_id': session.session_id,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'active_minutes': round(active_minutes, 2),
        }, status=status.HTTP_200_OK)


class StudySessionListAPIView(APIView):
    """
    Get all study sessions for the current user with statistics.
    Returns sessions with: time length, cards reviewed, average score.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        from django.db.models import Avg
        
        sessions = StudySession.objects.filter(user=request.user).order_by('-start_time')
        
        sessions_data = []
        for session in sessions:
            # Get reviews for this session
            reviews = session.card_reviews.all()
            cards_reviewed = reviews.count()
            
            # Calculate average score
            avg_score = None
            if cards_reviewed > 0:
                avg_score = reviews.aggregate(Avg('user_score'))['user_score__avg']
            
            # Calculate active minutes
            if session.is_active:
                active_minutes = session.calculate_active_minutes()
            else:
                active_minutes = session.calculate_active_minutes() if session.end_time else 0
            
            sessions_data.append({
                'session_id': session.session_id,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'is_active': session.is_active,
                'active_minutes': round(active_minutes, 2),
                'active_seconds': int(active_minutes * 60),
                'cards_reviewed': cards_reviewed,
                'average_score': round(avg_score, 3) if avg_score else None,
            })
        
        return Response({
            'sessions': sessions_data,
            'total_sessions': len(sessions_data),
        }, status=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    """
    API endpoint to get the current authenticated user information.
    Useful for verifying authentication is working correctly.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Return information about the currently authenticated user.
        """
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_authenticated': user.is_authenticated,
            'is_anonymous': user.is_anonymous,
        }, status=status.HTTP_200_OK)


class LessonListCreateAPIView(UserScopedMixin, ListCreateAPIView):
    """
    List or create lessons.
    POST: Create a new lesson (tokenizes automatically).
    """
    queryset = Lesson.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LessonCreateSerializer
        return LessonSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LessonDetailAPIView(UserScopedMixin, RetrieveAPIView):
    """
    Get lesson details with tokens.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonDetailSerializer
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]


class TranslateAPIView(APIView):
    """
    Translate text (word or sentence).
    POST: {text, source_lang, target_lang}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        from .translation_service import translate_text
        
        serializer = TranslateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        text = serializer.validated_data['text']
        source_lang = serializer.validated_data.get('source_lang', 'de')
        target_lang = serializer.validated_data.get('target_lang', 'en')
        
        translation = translate_text(text, source_lang, target_lang)
        
        if translation:
            return Response({
                'text': text,
                'translation': translation,
                'source_lang': source_lang,
                'target_lang': target_lang,
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Translation failed. Check API key configuration.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TokenClickAPIView(APIView):
    """
    Record a token click and return translation.
    GET: /api/flashcards/reader/tokens/<token_id>/click/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, token_id, *args, **kwargs):
        from .translation_service import translate_text, get_word_translation
        
        try:
            token = Token.objects.get(token_id=token_id, lesson__user=request.user)
        except Token.DoesNotExist:
            return Response({'error': 'Token not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Increment click count
        token.clicked_count += 1
        token.save(update_fields=['clicked_count'])
        
        # Get translation if not cached
        if not token.translation:
            word_translation = get_word_translation(token.text, token.lesson.language, 'en')
            if word_translation:
                token.translation = word_translation.get('translation', '')
                token.save(update_fields=['translation'])
        
        # Get sentence translation (for context)
        lesson = token.lesson
        sentence_text = self._get_sentence_context(lesson.text, token.start_offset)
        sentence_translation = None
        if sentence_text in lesson.sentence_translations:
            sentence_translation = lesson.sentence_translations[sentence_text]
        else:
            sentence_translation = translate_text(sentence_text, lesson.language, 'en')
            if sentence_translation:
                lesson.sentence_translations[sentence_text] = sentence_translation
                lesson.save(update_fields=['sentence_translations'])
        
        return Response({
            'token': TokenSerializer(token).data,
            'sentence': sentence_text,
            'sentence_translation': sentence_translation,
        }, status=status.HTTP_200_OK)
    
    def _get_sentence_context(self, text: str, offset: int) -> str:
        """Extract sentence containing the token."""
        # Find sentence boundaries
        sentence_end = text.find('.', offset)
        sentence_start = text.rfind('.', 0, offset) + 1
        if sentence_start == 0:
            sentence_start = 0
        if sentence_end == -1:
            sentence_end = len(text)
        else:
            sentence_end += 1
        
        return text[sentence_start:sentence_end].strip()


class AddToFlashcardsAPIView(APIView):
    """
    Add a token/phrase to flashcards.
    Creates a Card via existing Card API.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = AddToFlashcardsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        token_id = data.get('token_id')
        phrase_id = data.get('phrase_id')
        front = data['front']
        back = data['back']
        sentence_context = data.get('sentence_context', '')
        lesson_id = data['lesson_id']
        
        # Get lesson
        try:
            lesson = Lesson.objects.get(lesson_id=lesson_id, user=request.user)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get sentence translation if available
        sentence_translation = None
        if sentence_context:
            # Check if we have a cached translation for this sentence
            if sentence_context in lesson.sentence_translations:
                sentence_translation = lesson.sentence_translations[sentence_context]
            else:
                # Try to get translation
                from .translation_service import translate_text
                sentence_translation = translate_text(sentence_context, lesson.language, 'en')
                if sentence_translation:
                    lesson.sentence_translations[sentence_context] = sentence_translation
                    lesson.save(update_fields=['sentence_translations'])
        
        # Format notes with context and translation
        notes_parts = [f"From lesson: {lesson.title}"]
        if sentence_context:
            notes_parts.append(f"\n\nContext: {sentence_context}")
            if sentence_translation:
                notes_parts.append(f"\nTranslation: {sentence_translation}")
        
        # Create Card using existing CardCreateSerializer logic
        card_data = {
            'front': front,
            'back': back,
            'language': lesson.language,
            'tags': ['reader'],
            'notes': ''.join(notes_parts),
            'source': lesson.source_url or f"Lesson {lesson.lesson_id}",
            'create_reverse': True,
        }
        
        # Use existing Card creation endpoint logic
        card_serializer = CardCreateSerializer(data=card_data, context={'request': request})
        if not card_serializer.is_valid():
            return Response(card_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        card = card_serializer.save(user=request.user)
        
        # Update token/phrase
        if token_id:
            try:
                token = Token.objects.get(token_id=token_id, lesson=lesson)
                token.added_to_flashcards = True
                token.card_id = card.card_id
                token.save(update_fields=['added_to_flashcards', 'card_id'])
            except Token.DoesNotExist:
                pass
        
        if phrase_id:
            try:
                phrase = Phrase.objects.get(phrase_id=phrase_id, lesson=lesson)
                phrase.added_to_flashcards = True
                phrase.card_id = card.card_id
                phrase.save(update_fields=['added_to_flashcards', 'card_id'])
            except Phrase.DoesNotExist:
                pass
        
        return Response({
            'card_id': card.card_id,
            'message': 'Card created successfully',
        }, status=status.HTTP_201_CREATED)


class GenerateTTSAPIView(APIView):
    """
    Generate TTS audio for a lesson or text snippet.
    POST: {lesson_id, text (optional), language_code (optional)}
    """
    permission_classes = [IsAuthenticated]
    
    def _get_language_code(self, language):
        """Map language code to TTS format (e.g., 'de' -> 'de-DE', 'es' -> 'es-ES')."""
        language_map = {
            'de': 'de-DE',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'it': 'it-IT',
            'pt': 'pt-PT',
            'ru': 'ru-RU',
            'ja': 'ja-JP',
            'zh': 'zh-CN',
            'ko': 'ko-KR',
            'en': 'en-US',
        }
        return language_map.get(language.lower(), f"{language}-{language.upper()}")
    
    def post(self, request, *args, **kwargs):
        from .tts_service import generate_tts_audio
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"TTS API called - User: {request.user}, Data: {request.data}")
        
        lesson_id = request.data.get('lesson_id')
        text = request.data.get('text')
        language_code = request.data.get('language_code')
        
        if lesson_id:
            try:
                lesson = Lesson.objects.get(lesson_id=lesson_id, user=request.user)
                text = lesson.text
                if not language_code:
                    language_code = self._get_language_code(lesson.language)
                logger.info(f"Found lesson {lesson_id}, text length: {len(text)}, language_code: {language_code}")
            except Lesson.DoesNotExist:
                logger.error(f"Lesson {lesson_id} not found for user {request.user}")
                return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not text:
            logger.error("No text provided for TTS generation")
            return Response({'error': 'text or lesson_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not language_code:
            language_code = 'de-DE'  # Default fallback
        
        logger.info(f"Generating TTS for text length {len(text)}, language: {language_code}")
        audio_url = generate_tts_audio(text, language_code)
        
        if audio_url:
            logger.info(f"TTS generated successfully: {audio_url}")
            # Update lesson audio_url if lesson_id provided
            if lesson_id:
                lesson.audio_url = audio_url
                lesson.save(update_fields=['audio_url'])
                logger.info(f"Updated lesson {lesson_id} with audio_url: {audio_url}")
            
            return Response({
                'audio_url': audio_url,
                'lesson_id': lesson_id,
                'message': 'TTS audio generated successfully'
            }, status=status.HTTP_200_OK)
        else:
            error_msg = 'TTS generation failed. Check API configuration (GOOGLE_TTS_CREDENTIALS_PATH or ELEVENLABS_API_KEY).'
            logger.error(f"TTS Error: {error_msg}")
            print(f"TTS Error: {error_msg}")
            return Response(
                {'error': error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateListeningTimeAPIView(APIView):
    """
    Update listening time for a lesson.
    POST: {lesson_id, seconds_listened}
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        lesson_id = request.data.get('lesson_id')
        seconds_listened = request.data.get('seconds_listened', 0)
        
        if not lesson_id:
            return Response({'error': 'lesson_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            lesson = Lesson.objects.get(lesson_id=lesson_id, user=request.user)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update listening time
        lesson.total_listening_time_seconds += int(seconds_listened)
        from django.utils import timezone
        lesson.last_listened_at = timezone.now()
        lesson.save(update_fields=['total_listening_time_seconds', 'last_listened_at'])
        
        return Response({
            'lesson_id': lesson.lesson_id,
            'total_listening_time_seconds': lesson.total_listening_time_seconds,
            'last_listened_at': lesson.last_listened_at,
        }, status=status.HTTP_200_OK)
