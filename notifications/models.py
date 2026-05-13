from django.db import models
from queue_manager.models import QueueEntry


class NotificationLog(models.Model):
    TYPES = [
        ('queue_joined', 'Joined Queue'),
        ('two_ahead', 'Two Ahead'),
        ('you_are_next', 'You Are Next'),
        ('table_ready', 'Table Ready'),
        ('no_show_warn', 'No Show Warning'),
        ('feedback', 'Feedback Request'),
        ('delay_update', 'Delay Update'),
    ]

    CHANNELS = [
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]

    STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    queue_entry = models.ForeignKey(
        QueueEntry,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    # One queue entry → many notifications over its lifetime
    # joined → 2 ahead → you're next → table ready → feedback

    notification_type = models.CharField(max_length=30, choices=TYPES)
    channel = models.CharField(max_length=10, choices=CHANNELS, default='sms')
    message = models.TextField()
    # Actual SMS text that was sent

    status = models.CharField(max_length=20, choices=STATUS, default='pending')

    sent_at = models.DateTimeField(auto_now_add=True)

    twilio_sid = models.CharField(max_length=64, blank=True)
    # Twilio gives a unique ID for every SMS sent
    # Store it so we can check delivery status later
    # Example: SM1234567890abcdef

    def __str__(self):
        return f"{self.notification_type} → {self.queue_entry.customer.phone}"


class Feedback(models.Model):
    queue_entry = models.OneToOneField(
        QueueEntry,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    # OneToOneField → one visit gets exactly ONE feedback
    # Can't submit feedback twice for same visit

    overall_rating = models.IntegerField(
        validators=[
            __import__('django.core.validators', fromlist=['MinValueValidator']).MinValueValidator(1),
            __import__('django.core.validators', fromlist=['MaxValueValidator']).MaxValueValidator(5)
        ]
    )
    wait_satisfaction = models.IntegerField(
        validators=[
            __import__('django.core.validators', fromlist=['MinValueValidator']).MinValueValidator(1),
            __import__('django.core.validators', fromlist=['MaxValueValidator']).MaxValueValidator(5)
        ]
    )
    food_rating = models.IntegerField(
        validators=[
            __import__('django.core.validators', fromlist=['MinValueValidator']).MinValueValidator(1),
            __import__('django.core.validators', fromlist=['MaxValueValidator']).MaxValueValidator(5)
        ]
    )
    service_rating = models.IntegerField(
        validators=[
            __import__('django.core.validators', fromlist=['MinValueValidator']).MinValueValidator(1),
            __import__('django.core.validators', fromlist=['MaxValueValidator']).MaxValueValidator(5)
        ]
    )
    would_recommend = models.BooleanField(null=True)
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.queue_entry.token_number} - {self.overall_rating}★"
