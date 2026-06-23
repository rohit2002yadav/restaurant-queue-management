from rest_framework import serializers
from .models import Feedback, NotificationLog


class FeedbackSerializer(serializers.ModelSerializer):
    token_number = serializers.CharField(
        source='queue_entry.token_number', read_only=True
    )
    customer_name = serializers.CharField(
        source='queue_entry.customer.name', read_only=True
    )

    class Meta:
        model = Feedback
        fields = [
            'id',
            'token_number',
            'customer_name',
            'overall_rating',
            'wait_satisfaction',
            'food_rating',
            'service_rating',
            'would_recommend',
            'comment',
            'submitted_at',
        ]
        read_only_fields = ['id', 'submitted_at', 'token_number', 'customer_name']


class SubmitFeedbackSerializer(serializers.Serializer):
    token_number = serializers.CharField(max_length=10)
    overall_rating = serializers.IntegerField(min_value=1, max_value=5)
    wait_satisfaction = serializers.IntegerField(min_value=1, max_value=5)
    food_rating = serializers.IntegerField(min_value=1, max_value=5)
    service_rating = serializers.IntegerField(min_value=1, max_value=5)
    would_recommend = serializers.BooleanField(required=False, allow_null=True, default=None)
    comment = serializers.CharField(required=False, allow_blank=True, max_length=1000, default='')


class NotificationLogSerializer(serializers.ModelSerializer):
    token_number = serializers.CharField(
        source='queue_entry.token_number', read_only=True
    )

    class Meta:
        model = NotificationLog
        fields = [
            'id',
            'token_number',
            'notification_type',
            'channel',
            'message',
            'status',
            'sent_at',
        ]
