from rest_framework import serializers
from .models import MenuItem, OrderRecord, OrderItem


# =========================================================
# MENU ITEM SERIALIZER
# =========================================================
class MenuItemSerializer(serializers.ModelSerializer):
    """Display menu items available for ordering"""

    class Meta:
        model = MenuItem
        fields = [
            'id',
            'name',
            'category',
            'price',
            'base_prep_time_mins',
            'is_available',
            'is_veg',
            'description',
        ]


# =========================================================
# ORDER ITEM SERIALIZER (Items within an order)
# =========================================================
class OrderItemSerializer(serializers.ModelSerializer):
    """Display individual items in an order"""

    menu_item_name = serializers.CharField(
        source='menu_item.name',
        read_only=True
    )
    menu_item_category = serializers.CharField(
        source='menu_item.category',
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'menu_item',
            'menu_item_name',
            'menu_item_category',
            'quantity',
            'unit_price',
            'status',
            'special_notes',
            'subtotal',
        ]
        read_only_fields = ['id', 'subtotal']


# =========================================================
# CREATE ORDER ITEM INPUT SERIALIZER
# =========================================================
class CreateOrderItemSerializer(serializers.Serializer):
    """Input for adding items to an order"""

    menu_item_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=100)
    special_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


# =========================================================
# ORDER RECORD SERIALIZER (Full order with items)
# =========================================================
class OrderRecordSerializer(serializers.ModelSerializer):
    """Display complete order with all items"""

    items = OrderItemSerializer(many=True, read_only=True)
    token_number = serializers.CharField(
        source='table_assignment.queue_entry.token_number',
        read_only=True
    )
    customer_name = serializers.CharField(
        source='table_assignment.queue_entry.customer.name',
        read_only=True
    )
    table_number = serializers.CharField(
        source='table_assignment.table_unit.table_number',
        read_only=True
    )

    class Meta:
        model = OrderRecord
        fields = [
            'id',
            'token_number',
            'customer_name',
            'table_number',
            'status',
            'items',
            'total_amount',
            'notes',
            'placed_at',
            'estimated_ready_at',
            'delivered_at',
        ]
        read_only_fields = [
            'id',
            'placed_at',
            'delivered_at',
            'token_number',
            'customer_name',
            'table_number',
        ]


# =========================================================
# CREATE ORDER INPUT SERIALIZER
# =========================================================
class CreateOrderSerializer(serializers.Serializer):
    """Input for creating a new order"""

    table_assignment_id = serializers.IntegerField(min_value=1)
    items = CreateOrderItemSerializer(many=True)
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item")
        return value


# =========================================================
# UPDATE ORDER STATUS SERIALIZER
# =========================================================
class UpdateOrderStatusSerializer(serializers.Serializer):
    """Input for updating order status"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
    ]

    status = serializers.ChoiceField(choices=STATUS_CHOICES)


# =========================================================
# UPDATE ORDER ITEM STATUS SERIALIZER
# =========================================================
class UpdateOrderItemStatusSerializer(serializers.Serializer):
    """Input for updating individual item status"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
    ]

    status = serializers.ChoiceField(choices=STATUS_CHOICES)
