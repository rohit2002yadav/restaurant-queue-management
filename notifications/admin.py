from django.contrib import admin
from .models import NotificationLog, Feedback


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification_type', 'channel', 'status', 'sent_at', 'queue_entry']
    list_filter = ['notification_type', 'channel', 'status']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['queue_entry', 'overall_rating', 'food_rating', 'service_rating', 'wait_satisfaction', 'submitted_at']
    list_filter = ['overall_rating', 'would_recommend']
