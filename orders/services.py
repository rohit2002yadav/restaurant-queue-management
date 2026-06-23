from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F
from datetime import timedelta
import logging

from .models import MenuItem, OrderRecord, OrderItem
from queue_manager.models import TableAssignment

logger = logging.getLogger(__name__)


# =========================================================
# GET MENU BY RESTAURANT
# =========================================================
def get_menu_by_restaurant(restaurant_id):
    """
    Fetch available menu items for a restaurant

    Args:
        restaurant_id: ID of restaurant

    Returns:
        QuerySet of MenuItem objects
    """
    return MenuItem.objects.filter(
        restaurant_id=restaurant_id,
        is_available=True
    ).order_by('category', 'name')


# =========================================================
# CALCULATE ESTIMATED READY TIME
# =========================================================
def calculate_estimated_ready_time(items_data):
    """
    Calculate when food will be ready based on prep times and quantities

    The logic: max prep time + buffer for simultaneous cooking

    Example:
    - Burger (10 min, qty 2)
    - Salad (5 min, qty 1)
    Result: max(10, 5) = 10 minutes

    Args:
        items_data: List of {'menu_item': MenuItem, 'quantity': int}

    Returns:
        timedelta object
    """
    max_prep_time = 0

    for item in items_data:
        base_time = item['menu_item'].base_prep_time_mins
        qty = item['quantity']

        # Simple formula: base_time + (qty - 1) * 2 minutes per extra item
        # This accounts for parallel cooking with slight delay per item
        estimated_item_time = base_time + (qty - 1) * 2

        max_prep_time = max(max_prep_time, estimated_item_time)

    return timedelta(minutes=max_prep_time)


# =========================================================
# CREATE ORDER WITH ITEMS
# =========================================================
@transaction.atomic
def create_order_service(table_assignment_id, items_data, notes=''):
    """
    Create a new order with items

    Args:
        table_assignment_id: ID of TableAssignment (which customer, which table)
        items_data: List of {'menu_item_id': int, 'quantity': int, 'special_notes': str}
        notes: Order-level notes (optional)

    Returns:
        {
            'order_id': int,
            'status': 'pending',
            'items': [...],
            'total_amount': Decimal,
            'estimated_ready_at': datetime,
        }

    Raises:
        ValueError: If table_assignment invalid, menu items not found, etc.
    """

    # 1️⃣ Get table assignment (validates it exists and is active)
    try:
        assignment = TableAssignment.objects.select_related(
            'table_unit',
            'queue_entry__restaurant'
        ).get(
            id=table_assignment_id,
            is_active=True
        )
    except TableAssignment.DoesNotExist:
        raise ValueError("Active table assignment not found")

    restaurant = assignment.queue_entry.restaurant

    # 2️⃣ Fetch all menu items (validate they exist and are available)
    menu_item_ids = [item['menu_item_id'] for item in items_data]
    menu_items_map = {
        item.id: item
        for item in MenuItem.objects.filter(
            id__in=menu_item_ids,
            restaurant=restaurant,
            is_available=True
        )
    }

    if len(menu_items_map) != len(menu_item_ids):
        raise ValueError("One or more menu items not found or not available")

    # 3️⃣ Calculate total amount and prep time
    total_amount = 0
    items_with_prices = []

    for item in items_data:
        menu_item = menu_items_map[item['menu_item_id']]
        quantity = item['quantity']
        unit_price = menu_item.price

        subtotal = unit_price * quantity
        total_amount += subtotal

        items_with_prices.append({
            'menu_item': menu_item,
            'quantity': quantity,
            'unit_price': unit_price,
            'special_notes': item.get('special_notes', ''),
            'subtotal': subtotal,
        })

    estimated_prep_time = calculate_estimated_ready_time(items_with_prices)
    estimated_ready_at = timezone.now() + estimated_prep_time

    # 4️⃣ Create order
    order = OrderRecord.objects.create(
        table_assignment=assignment,
        status='pending',
        notes=notes,
        total_amount=total_amount,
        estimated_ready_at=estimated_ready_at,
    )

    logger.info(f"Created order {order.id} for table {assignment.table_unit.table_number}")

    # 5️⃣ Create order items
    order_items = []
    for item_data in items_with_prices:
        order_item = OrderItem.objects.create(
            order=order,
            menu_item=item_data['menu_item'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],
            special_notes=item_data['special_notes'],
            status='pending',
        )
        order_items.append(order_item)

    logger.info(f"Added {len(order_items)} items to order {order.id}")

    return {
        'order_id': order.id,
        'status': order.status,
        'total_amount': str(total_amount),
        'estimated_ready_at': estimated_ready_at,
        'items_count': len(order_items),
    }


# =========================================================
# UPDATE ORDER STATUS
# =========================================================
@transaction.atomic
def update_order_status_service(order_id, new_status):
    """
    Update order status and set timestamps

    Args:
        order_id: ID of OrderRecord
        new_status: New status (pending, confirmed, preparing, ready, delivered, completed)

    Returns:
        {'order_id': int, 'status': str, 'message': str}

    Raises:
        ValueError: If order not found or invalid status transition
    """

    try:
        order = OrderRecord.objects.get(id=order_id)
    except OrderRecord.DoesNotExist:
        raise ValueError("Order not found")

    # Validate status
    valid_statuses = [choice[0] for choice in OrderRecord.STATUS]
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    old_status = order.status
    order.status = new_status

    # Set delivered_at timestamp when marking as delivered
    if new_status == 'delivered' and not order.delivered_at:
        order.delivered_at = timezone.now()

    order.save(update_fields=['status', 'delivered_at'])

    logger.info(f"Updated order {order_id} status: {old_status} → {new_status}")

    return {
        'order_id': order.id,
        'status': order.status,
        'message': f"Order status updated to {new_status}",
    }


# =========================================================
# UPDATE ORDER ITEM STATUS
# =========================================================
@transaction.atomic
def update_order_item_status_service(order_item_id, new_status):
    """
    Update individual item status

    Args:
        order_item_id: ID of OrderItem
        new_status: New status (pending, preparing, ready, served)

    Returns:
        {'item_id': int, 'status': str, 'message': str}

    Raises:
        ValueError: If item not found or invalid status
    """

    try:
        item = OrderItem.objects.get(id=order_item_id)
    except OrderItem.DoesNotExist:
        raise ValueError("Order item not found")

    # Validate status
    valid_statuses = [choice[0] for choice in OrderItem.STATUS]
    if new_status not in valid_statuses:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    old_status = item.status
    item.status = new_status
    item.save(update_fields=['status'])

    logger.info(f"Updated order item {order_item_id} status: {old_status} → {new_status}")

    return {
        'item_id': item.id,
        'status': item.status,
        'message': f"Item status updated to {new_status}",
    }


# =========================================================
# GET ORDERS FOR TABLE ASSIGNMENT
# =========================================================
def get_orders_for_table_service(table_assignment_id):
    """
    Fetch all orders for a specific table

    Args:
        table_assignment_id: ID of TableAssignment

    Returns:
        List of orders with items

    Raises:
        ValueError: If table assignment not found
    """

    try:
        assignment = TableAssignment.objects.get(id=table_assignment_id)
    except TableAssignment.DoesNotExist:
        raise ValueError("Table assignment not found")

    orders = OrderRecord.objects.filter(
        table_assignment=assignment
    ).prefetch_related('items__menu_item').order_by('-placed_at')

    return orders


# =========================================================
# GET ACTIVE ORDERS FOR RESTAURANT
# =========================================================
def get_active_orders_service(restaurant_id):
    """
    Fetch all active (non-completed) orders for a restaurant

    Used by kitchen staff to see what's being prepared

    Args:
        restaurant_id: ID of Restaurant

    Returns:
        List of orders with status not in (delivered, completed)
    """

    return OrderRecord.objects.filter(
        table_assignment__queue_entry__restaurant_id=restaurant_id,
        status__in=['pending', 'confirmed', 'preparing', 'ready']
    ).select_related(
        'table_assignment__table_unit',
        'table_assignment__queue_entry__customer'
    ).prefetch_related('items__menu_item').order_by('placed_at')


# =========================================================
# MARK ORDER AS READY (Helper)
# =========================================================
@transaction.atomic
def mark_order_ready_service(order_id):
    """
    Transition order from preparing → ready

    Called when kitchen finishes preparing items

    Args:
        order_id: ID of OrderRecord

    Returns:
        Order object
    """

    try:
        order = OrderRecord.objects.get(id=order_id, status='preparing')
    except OrderRecord.DoesNotExist:
        raise ValueError("Order not found or not in preparing state")

    order.status = 'ready'
    order.save(update_fields=['status'])

    logger.info(f"Marked order {order_id} as ready")

    return order
