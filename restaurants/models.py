from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Restaurant(models.Model):
    # Basic restaurant info
    name = models.CharField(max_length=100)
    # Short text field for restaurant name

    phone = models.CharField(
        max_length=10,
        unique=True,  # No two restaurants can have same phone
        validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message="Enter a valid Indian phone number"
            )
        ]
    )
    # Stored as string because phone numbers are identifiers, not numbers

    address = models.TextField()
    # Long text field for full address

    opening_time = models.TimeField()
    closing_time = models.TimeField()
    # Used to check if restaurant is open or closed

    avg_meal_duration_mins = models.IntegerField(
        default=45,
        validators=[MinValueValidator(10), MaxValueValidator(300)]
    )
    # Used to estimate wait time
    # Example: if avg = 45 mins, system predicts table availability

    max_queue_size = models.IntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(500)]
    )
    # Prevents system overload (too many people in queue)

    is_active = models.BooleanField(default=True)
    # If False → restaurant is disabled (no new entries)

    created_at = models.DateTimeField(auto_now_add=True)
    # Automatically set when record is created

    def clean(self):
        # Custom validation: opening time must be before closing time
        if self.opening_time >= self.closing_time:
            raise ValidationError("Opening time must be before closing time")

    def __str__(self):
        # What shows in admin panel
        return self.name


class TableUnit(models.Model):
    # Possible states of a table
    STATUS = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('cleaning', 'Cleaning'),
        ('inactive', 'Inactive'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='tables'
    )
    # Each table belongs to one restaurant
    # If restaurant is deleted → all tables are deleted

    table_number = models.CharField(max_length=10)
    # Example: T1, T2, A5

    capacity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    # Number of people that can sit
    # Validation prevents invalid values like 0 or negative

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='available'
    )
    # Current state of table (important for allocation logic)

    is_combinable = models.BooleanField(default=True)
    # Can this table be merged with another?
    # Used for large groups (e.g., combine 2 tables for 6 people)

    section = models.CharField(max_length=50, blank=True)
    # Optional: helps categorize tables
    # Example: window, outdoor, VIP

    notes = models.TextField(blank=True)
    # Optional extra info (e.g., broken chair, near AC)

    class Meta:
        # Prevent duplicate table numbers in same restaurant
        unique_together = [('restaurant', 'table_number')]

        # Database-level safety: capacity must always be > 0
        constraints = [
            models.CheckConstraint(
                check=models.Q(capacity__gt=0),
                name='capacity_positive'
            )
        ]

    def __str__(self):
        # Readable format in admin panel
        return f"Table {self.table_number} ({self.capacity} seats) - {self.restaurant.name}"