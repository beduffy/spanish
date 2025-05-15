from django.urls import path
from .views import NextCardAPIView, SubmitReviewAPIView

app_name = 'flashcards'

urlpatterns = [
    path('next-card/', NextCardAPIView.as_view(), name='next_card_api'),
    path('submit-review/', SubmitReviewAPIView.as_view(), name='submit_review_api'),
    # Other flashcard app API endpoints will go here
] 