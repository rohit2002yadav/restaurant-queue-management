import re
from rest_framework import serializers
from .models import Customer, QueueEntry, TableAssignment

INDIAN_PHONE_RE = re.compile(r'^[6-9]\d{9}$')


# =========================================================
# CUSTOMER SERIALIZER
# Purpose:
# Converts Customer model → JSON (for API responses)
# =========================================================
class CustomerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customer

        fields = ['id', 'name', 'phone', 'visit_count']
        # WHAT:
        # → Defines which fields are exposed in API response

        # WHY:
        # → We only expose useful fields to frontend
        # → We hide internal fields like created_at (not needed for user)


# =========================================================
# JOIN QUEUE SERIALIZER (INPUT SERIALIZER)
# Purpose:
# Validates data when customer joins queue
# =========================================================
class JoinQueueSerializer(serializers.Serializer):
    # WHY NOT ModelSerializer?
    # → Because this handles MULTIPLE models:
    #    - Customer (create/update)
    #    - QueueEntry (create)
    # → So we use plain Serializer for custom logic

    name = serializers.CharField(max_length=100)
    # WHAT:
    # → Customer name input

    phone = serializers.CharField(max_length=10)
    # WHAT:
    # → Customer phone input
    # WHY:
    # → Used to identify or create customer

    party_size = serializers.IntegerField(min_value=1, max_value=20)
    # WHAT:
    # → Number of people
    # WHY:
    # → Needed for table matching logic

    special_request = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )
    # WHAT:
    # → Optional field (e.g., "window seat")
    # WHY:
    # → Improves customer experience
    # required=False → not mandatory
    # allow_blank=True → "" allowed

    def validate_phone(self, value):
        if not INDIAN_PHONE_RE.match(value):
            raise serializers.ValidationError(
                "Enter a valid 10 digit Indian mobile number"
            )
        return value

    restaurant_id = serializers.IntegerField(min_value=1)


# =========================================================
# QUEUE ENTRY SERIALIZER (OUTPUT SERIALIZER)
# Purpose:
# Converts QueueEntry model → JSON (for frontend display)
# =========================================================
class QueueEntrySerializer(serializers.ModelSerializer):

    customer_name = serializers.CharField(
        source='customer.name',
        read_only=True
    )
    # WHAT:
    # → Pulls name from related Customer model

    # WHY:
    # → Avoids extra API call
    # → Frontend gets everything in one response

    customer_phone = serializers.CharField(
        source='customer.phone',
        read_only=True
    )
    # Same logic as above

    class Meta:
        model = QueueEntry

        fields = [
            'id',
            'token_number',
            'customer_name',
            'customer_phone',
            'party_size',
            'queue_type',
            'priority',
            'status',
            'joined_at',
            'called_at',
            'estimated_wait_mins',
            'special_request',
        ]

        # WHY THESE FIELDS:
        # → These are exactly what frontend needs to display queue info
        # → We exclude internal fields like:
        #    - expires_at
        #    - database-only fields


class TableAssignmentSerializer(serializers.ModelSerializer):
    token_number = serializers.CharField(
        source='queue_entry.token_number',
        read_only=True
    )
    customer_name = serializers.CharField(
        source='queue_entry.customer.name',
        read_only=True
    )
    customer_phone = serializers.CharField(
        source='queue_entry.customer.phone',
        read_only=True
    )
    party_size = serializers.IntegerField(
        source='queue_entry.party_size',
        read_only=True
    )
    table_number = serializers.CharField(
        source='table_unit.table_number',
        read_only=True
    )
    table_capacity = serializers.IntegerField(
        source='table_unit.capacity',
        read_only=True
    )
    entry_status = serializers.CharField(
        source='queue_entry.status',
        read_only=True
    )
    queue_entry_id = serializers.IntegerField(
        source='queue_entry.id',
        read_only=True
    )

    class Meta:
        model = TableAssignment
        fields = [
            'id',
            'queue_entry_id',
            'token_number',
            'customer_name',
            'customer_phone',
            'party_size',
            'table_number',
            'table_capacity',
            'assigned_at',
            'is_active',
            'entry_status',
        ]
