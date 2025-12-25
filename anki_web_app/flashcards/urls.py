from django.urls import path
from .views import (
    NextCardAPIView, 
    SubmitReviewAPIView, 
    StatisticsAPIView, 
    SentenceListAPIView,
    SentenceDetailAPIView,
    CardListCreateAPIView,
    CardDetailAPIView,
    CardNextCardAPIView,
    CardSubmitReviewAPIView,
    CardStatisticsAPIView,
    CardUpdateAPIView,
    CardDeleteAPIView,
    CardImportAPIView,
    StudySessionStartAPIView,
    StudySessionHeartbeatAPIView,
    StudySessionEndAPIView,
    StudySessionListAPIView,
)

app_name = 'flashcards'

urlpatterns = [
    path('next-card/', NextCardAPIView.as_view(), name='next_card_api'),
    path('submit-review/', SubmitReviewAPIView.as_view(), name='submit_review_api'),
    path('statistics/', StatisticsAPIView.as_view(), name='statistics_api'),
    path('sentences/', SentenceListAPIView.as_view(), name='sentence_list_api'),
    path('sentences/<int:pk>/', SentenceDetailAPIView.as_view(), name='sentence_detail_api'),
    path('cards/', CardListCreateAPIView.as_view(), name='card_list_create_api'),
    path('cards/<int:pk>/', CardDetailAPIView.as_view(), name='card_detail_api'),
    path('cards/<int:pk>/update/', CardUpdateAPIView.as_view(), name='card_update_api'),
    path('cards/<int:pk>/delete/', CardDeleteAPIView.as_view(), name='card_delete_api'),
    path('cards/import/', CardImportAPIView.as_view(), name='card_import_api'),
    path('cards/next-card/', CardNextCardAPIView.as_view(), name='card_next_card_api'),
    path('cards/submit-review/', CardSubmitReviewAPIView.as_view(), name='card_submit_review_api'),
    path('cards/statistics/', CardStatisticsAPIView.as_view(), name='card_statistics_api'),
    # Study session endpoints (Phase 5)
    path('sessions/', StudySessionListAPIView.as_view(), name='study_session_list_api'),
    path('sessions/start/', StudySessionStartAPIView.as_view(), name='study_session_start_api'),
    path('sessions/heartbeat/', StudySessionHeartbeatAPIView.as_view(), name='study_session_heartbeat_api'),
    path('sessions/end/', StudySessionEndAPIView.as_view(), name='study_session_end_api'),
    # Other flashcard app API endpoints will go here
] 