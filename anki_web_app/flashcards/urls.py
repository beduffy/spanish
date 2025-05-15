from django.urls import path
from .views import (
    NextCardAPIView, 
    SubmitReviewAPIView, 
    StatisticsAPIView, 
    SentenceListAPIView,
    SentenceDetailAPIView
)

app_name = 'flashcards'

urlpatterns = [
    path('next-card/', NextCardAPIView.as_view(), name='next_card_api'),
    path('submit-review/', SubmitReviewAPIView.as_view(), name='submit_review_api'),
    path('statistics/', StatisticsAPIView.as_view(), name='statistics_api'),
    path('sentences/', SentenceListAPIView.as_view(), name='sentence_list_api'),
    path('sentences/<int:pk>/', SentenceDetailAPIView.as_view(), name='sentence_detail_api'),
    # Other flashcard app API endpoints will go here
] 