from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from restaurants.models import Restaurant, TableUnit


# =========================================================
# CUSTOMER MODEL
# Purpose:
# Represents a real human visiting the restaurant.
# This is NOT authentication → just identity tracking.
# =========================================================
class Customer(models.Model):

    name = models.CharField(max_length=100)
    # WHAT: Stores customer name
    # WHY: Needed for display (staff dashboard, SMS, UI)

    phone = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message='Enter a valid 10 digit Indian mobile number'
            )
        ]
    )
    # WHAT: Stores phone number
    # WHY:
    # - Used as PRIMARY identity (no login system)
    # - unique=True prevents duplicate customers
    # - validation ensures clean data
    # IMPORTANT: stored as string, not number

    email = models.EmailField(blank=True)
    # WHAT: Optional email
    # WHY: Future use (notifications, login, marketing)

    visit_count = models.IntegerField(default=0)
    # WHAT: Count of visits
    # WHY:
    # - Can identify frequent customers
    # - Can be used for loyalty / VIP logic

    created_at = models.DateTimeField(auto_now_add=True)
    # WHAT: Timestamp when customer created
    # WHY:
    # - Helps track user history
    # - Useful for analytics

    def __str__(self):
        return f"{self.name} ({self.phone})"
        # WHY: readable display in admin


# =========================================================
# QUEUE ENTRY (CORE SYSTEM)
# Purpose:
# Represents ONE visit of a customer in the queue.
# This is the "brain" of your system.
# =========================================================
class QueueEntry(models.Model):

    # WHAT: Different stages of customer lifecycle
    # WHY: Helps track movement through system
    STATUS = [
        ('waiting', 'Waiting'),
        ('called', 'Called'),
        ('seated', 'Seated'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('left', 'Left Queue'),
    ]

    # WHAT: Queue segmentation
    # WHY:
    # - Prevents blocking problem
    # - 2-seater vs 4-seater queues separated
    QUEUE_TYPE = [
        ('small', '1-2'),
        ('medium', '3-4'),
        ('large', '5+'),
    ]

    # WHAT: Priority handling
    # WHY:
    # - VIP / elderly / special cases   
    PRIORITY = [
        ('normal', 'Normal'),
        ('high', 'High'),
        ('vip', 'VIP'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='queue_entries'
    )
    # WHAT: Which restaurant this entry belongs to
    # WHY:
    # - Multi-restaurant support
    # - CASCADE ensures cleanup if restaurant deleted

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='queue_entries'
    )
    # WHAT: Which customer this entry belongs to
    # WHY:
    # - PROTECT prevents deleting customer with history
    # - Maintains audit trail

    token_number = models.CharField(max_length=10)
    # WHAT: Token shown to customer (T-001)
    # WHY:
    # - Used for tracking
    # - Unique per restaurant (handled below)

    party_size = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    # WHAT: Number of people
    # WHY:
    # - Needed for table matching
    # - Validators prevent invalid values

    queue_type = models.CharField(
        max_length=10,
        choices=QUEUE_TYPE
    )
    # WHAT: Type of queue
    # WHY:
    # - Helps system pick correct table
    # - Avoids mismatch issues

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY,
        default='normal'
    )
    # WHAT: Priority level
    # WHY:
    # - Allows manual override in system

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='waiting'
    )
    # WHAT: Current state
    # WHY:
    # - Core logic depends on this
    # - Example: only 'waiting' entries are in queue

    # ---------- TIME TRACKING ----------
    # WHY: Needed for analytics + wait calculation

    joined_at = models.DateTimeField(auto_now_add=True)
    # When customer entered queue

    called_at = models.DateTimeField(null=True, blank=True)
    # When system notified customer

    seated_at = models.DateTimeField(null=True, blank=True)
    # When customer got table

    completed_at = models.DateTimeField(null=True, blank=True)
    # When customer finished meal

    expires_at = models.DateTimeField(null=True, blank=True)
    # WHY:
    # - Used for no-show handling
    # - Auto-remove inactive customers

    estimated_wait_mins = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(500)]
    )
    # WHAT: Estimated wait time
    # WHY:
    # - Shown to customer
    # - Updated dynamically

    special_request = models.TextField(blank=True)
    # WHAT: Custom request
    # WHY:
    # - Improves UX (window seat, etc)

    # ---------- META ----------
    class Meta:
        ordering = ['joined_at']
        # WHY:
        # - Ensures FIFO (first come first serve)
        # - Default ordering for queries

        indexes = [
            models.Index(fields=['restaurant', 'status']),
            models.Index(fields=['restaurant', 'queue_type', 'status']),
        ]
        # WHY:
        # - Improves query performance
        # - Critical when queue grows large

        constraints = [
            models.UniqueConstraint(
                fields=['restaurant', 'token_number'],
                name='unique_token_per_restaurant'
            )
        ]
        # WHY:
        # - Prevent duplicate tokens inside same restaurant

    def save(self, *args, **kwargs):
        # WHAT: Automatically assign queue_type
        # WHY:
        # - Prevent frontend mistakes
        # - Keeps data consistent
        if self.party_size <= 2:
            self.queue_type = 'small'
        elif self.party_size <= 4:
            self.queue_type = 'medium'
        else:
            self.queue_type = 'large'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.token_number} - {self.customer.name}"


# =========================================================
# TABLE ASSIGNMENT
# Purpose:
# Links queue entry to actual table (real-world mapping)
# =========================================================
class TableAssignment(models.Model):

    queue_entry = models.ForeignKey(
        QueueEntry,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    # WHAT: Which queue entry this belongs to
    # WHY:
    # - One customer can have history of assignments

    table_unit = models.ForeignKey(
        TableUnit,
        on_delete=models.PROTECT,
        related_name='assignments'
    )
    # WHAT: Which table is assigned
    # WHY:
    # - PROTECT keeps history intact

    assigned_at = models.DateTimeField(auto_now_add=True)
    # When table was given

    cleared_at = models.DateTimeField(null=True, blank=True)
    # When table became free

    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    # WHO assigned the table (staff)

    is_active = models.BooleanField(default=True)
    # WHAT:
    # - True → currently seated
    # - False → history
    # WHY:
    # - Needed because one customer can have past assignments

    def save(self, *args, **kwargs):
        # WHAT: Enforce rule in application logic
        # WHY:
        # - MySQL doesn't support conditional constraints
        # - So we manually enforce:
        #   "One customer can have only ONE active table"

        if self.is_active and not self.pk:
            already_exists = TableAssignment.objects.filter(
                queue_entry=self.queue_entry,
                is_active=True
            ).exists()

            if already_exists:
                raise ValueError("Customer already has an active table")

        super().save(*args, **kwargs)

    @property
    def meal_duration_mins(self):
        # WHAT: Calculate how long customer stayed
        # WHY:
        # - Used to improve future wait predictions
        if self.cleared_at:
            delta = self.cleared_at - self.assigned_at
            return int(delta.total_seconds() / 60)
        return None

    def __str__(self):
        return f"{self.queue_entry.token_number} → Table {self.table_unit.table_number}"