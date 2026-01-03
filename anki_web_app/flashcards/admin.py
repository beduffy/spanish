from django.contrib import admin
from .models import Card, CardReview, StudySession, SessionActivity, TokenStatus

# Register your models here.

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['card_id', 'front', 'back', 'user', 'is_learning', 'next_review_date', 'total_reviews']
    list_filter = ['is_learning', 'language', 'user']
    search_fields = ['front', 'back', 'notes']


@admin.register(CardReview)
class CardReviewAdmin(admin.ModelAdmin):
    list_display = ['review_id', 'card', 'review_timestamp', 'user_score', 'typed_input']
    list_filter = ['review_timestamp']
    search_fields = ['card__front', 'card__back', 'user_comment_addon']


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'start_time', 'end_time', 'is_active', 'last_activity_time']
    list_filter = ['is_active', 'start_time']
    search_fields = ['user__username', 'user__email']


@admin.register(SessionActivity)
class SessionActivityAdmin(admin.ModelAdmin):
    list_display = ['activity_id', 'session', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['session__user__username']


@admin.register(TokenStatus)
class TokenStatusAdmin(admin.ModelAdmin):
    list_display = ['status_id', 'user', 'token', 'status', 'updated_at']
    list_filter = ['status', 'updated_at']
    search_fields = ['user__username', 'token__text', 'token__normalized']
    readonly_fields = ['created_at', 'updated_at']
