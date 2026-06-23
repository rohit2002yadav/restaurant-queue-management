from django.utils import timezone
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
import logging
from .models import Customer, QueueEntry, TableAssignment
from restaurants.models import Restaurant, TableUnit

logger = logging.getLogger(__name__)



# =========================================================
# TOKEN GENERATION (SAFE VERSION)
# =========================================================
@transaction.atomic
def generate_token(restaurant_id):
    today = timezone.now().date()

    # Get last token number used today
    last_entry = QueueEntry.objects.select_for_update().filter(
        restaurant_id=restaurant_id,
        joined_at__date=today
    ).order_by('-id').first()

    if last_entry:
        new_number = int(last_entry.token_number.split('-')[1]) + 1
    else:
        new_number = 1

    # Safety check: keep incrementing if token already exists
    # (handles edge case of manually added tokens)
    while QueueEntry.objects.filter(
        restaurant_id=restaurant_id,
        token_number=f"T-{str(new_number).zfill(3)}"
    ).exists():
        new_number += 1

    return f"T-{str(new_number).zfill(3)}"


# =========================================================
# FIND BEST TABLE (MINIMUM WASTE STRATEGY)
# =========================================================
def find_best_table(restaurant, party_size):
    return TableUnit.objects.filter(
        restaurant=restaurant,
        capacity__gte=party_size,
        status='available'
    ).select_for_update().order_by('capacity').first()


# =========================================================
# CALCULATE WAIT TIME (IMPROVED LOGIC)
# =========================================================
def calculate_wait_time(restaurant, party_size, queue_entry=None):

    suitable_tables = TableUnit.objects.filter(
        restaurant=restaurant,
        capacity__gte=party_size
    )

    # If table available → no wait
    if suitable_tables.filter(status='available').exists():
        return 0

    # Determine queue type
    if party_size <= 2:
        queue_type = 'small'
    elif party_size <= 4:
        queue_type = 'medium'
    else:
        queue_type = 'large'

    waiting_entries = QueueEntry.objects.filter(
        restaurant=restaurant,
        status='waiting',
        queue_type=queue_type,
        expires_at__isnull=True
    )

    if queue_entry:
        waiting_entries = waiting_entries.filter(joined_at__lt=queue_entry.joined_at)

    people_ahead = waiting_entries.count()

    avg_time = restaurant.avg_meal_duration_mins

    occupied_count = suitable_tables.filter(status='occupied').count()

    if occupied_count == 0:
        return 0

    # Correct rounding logic
    rounds = people_ahead // occupied_count
    if people_ahead % occupied_count != 0:
        rounds += 1

    return rounds * avg_time


# =========================================================
# JOIN QUEUE (MAIN ENTRY POINT)
# =========================================================
@transaction.atomic
def join_queue_service(data):

    name = data.get('name')
    phone = data.get('phone')
    party_size = data.get('party_size')
    restaurant_id = data.get('restaurant_id')
    special_request = data.get('special_request', '')

    # 1️⃣ Get restaurant safely
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        raise ValueError("Restaurant not found")

    if not restaurant.is_active:
        raise ValueError("Restaurant is not accepting queue entries")

    active_queue_count = QueueEntry.objects.filter(
        restaurant=restaurant,
        status__in=['waiting', 'called']
    ).count()

    if active_queue_count >= restaurant.max_queue_size:
        raise ValueError("Queue is currently full")

    if not TableUnit.objects.filter(
        restaurant=restaurant,
        capacity__gte=party_size,
        status__in=['available', 'occupied', 'reserved', 'cleaning']
    ).exists():
        raise ValueError("No table can accommodate this party size")

    if Customer.objects.filter(
        phone=phone,
        queue_entries__restaurant=restaurant,
        queue_entries__status__in=['waiting', 'called', 'seated']
    ).exists():
        raise ValueError("Customer already has an active queue entry")

    # 2️⃣ Get or create customer
    customer, created = Customer.objects.get_or_create(
        phone=phone,
        defaults={'name': name}
    )
    if not created and customer.name != name:
        customer.name = name
        customer.save(update_fields=['name'])

    # 3️⃣ Generate token
    token = generate_token(restaurant_id)

    # 4️⃣ Find available table
    table = find_best_table(restaurant, party_size)

    # 5️⃣ Calculate wait time
    wait_time = calculate_wait_time(restaurant, party_size)

    # 6️⃣ Create queue entry
    queue_entry = QueueEntry.objects.create(
        restaurant=restaurant,
        customer=customer,
        token_number=token,
        party_size=party_size,
        estimated_wait_mins=wait_time,
        special_request=special_request
    )

    # 7️⃣ If table available → assign immediately
    if table:
        table.status = 'occupied'
        table.save()

        queue_entry.status = 'seated'
        queue_entry.seated_at = timezone.now()
        queue_entry.save()

        assignment = TableAssignment.objects.create(
            queue_entry=queue_entry,
            table_unit=table
        )
        customer.visit_count += 1
        customer.save(update_fields=['visit_count'])

        return {
            "message": "Table assigned immediately",
            "token": token,
            "status": queue_entry.status,
            "assignment_id": assignment.id,
            "table": table.table_number,
            "wait_time": 0
        }

    # 8️⃣ Otherwise → customer joins queue
    # Send SMS notification
    from notifications.services import notify_queue_joined
    try:
        notify_queue_joined(queue_entry.id)
    except Exception as e:
        logger.warning(f"Failed to send SMS notification: {str(e)}")

    return {
        "message": "Added to queue",
        "token": token,
        "status": queue_entry.status,
        "wait_time": wait_time
    }


def priority_order_expression():
    return Case(
        When(priority='vip', then=Value(0)),
        When(priority='high', then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )


def get_next_waiting_entry_for_table(restaurant, table):
    return QueueEntry.objects.select_for_update().filter(
        restaurant=restaurant,
        status='waiting',
        expires_at__isnull=True,
        party_size__lte=table.capacity
    ).annotate(
        priority_rank=priority_order_expression()
    ).order_by('priority_rank', 'joined_at').first()


def assign_table_and_call_customer(queue_entry, table):
    from datetime import timedelta

    now = timezone.now()

    table.status = 'occupied'
    table.save(update_fields=['status'])

    queue_entry.status = 'called'
    queue_entry.called_at = now
    queue_entry.expires_at = now + timedelta(minutes=10)
    queue_entry.save(update_fields=['status', 'called_at', 'expires_at'])

    assignment = TableAssignment.objects.create(
        queue_entry=queue_entry,
        table_unit=table
    )

    return assignment


@transaction.atomic
def clear_table_service(table_assignment_id):
    # 1️⃣ Get active assignment with lock
    try:
        assignment = TableAssignment.objects.select_related(
            'table_unit',
            'queue_entry__restaurant'
        ).select_for_update().get(
            id=table_assignment_id,
            is_active=True
        )
    except TableAssignment.DoesNotExist:
        raise ValueError("Active table assignment not found")

    # 2️⃣ Mark assignment as cleared
    assignment.cleared_at = timezone.now()
    assignment.is_active = False
    assignment.save(update_fields=['cleared_at', 'is_active'])

    # 3️⃣ Mark queue entry as completed
    queue_entry = assignment.queue_entry
    queue_entry.status = 'completed'
    queue_entry.completed_at = timezone.now()
    queue_entry.save(update_fields=['status', 'completed_at'])

    # 4️⃣ Get table + restaurant
    table = assignment.table_unit
    restaurant = queue_entry.restaurant

    # ⚠️ TEMPORARILY FREE TABLE BEFORE REASSIGNING
    table.status = 'available'
    table.save(update_fields=['status'])

    # 5️⃣ Find next suitable customer
    next_entry = get_next_waiting_entry_for_table(restaurant, table)

    if next_entry:
        # 6️⃣ Assign table and call customer
        new_assignment = assign_table_and_call_customer(next_entry, table)

        # 7️⃣ Update wait times
        recalculate_wait_times(restaurant)

        return {
            "message": "Table cleared and next customer called",
            "table": table.table_number,
            "assignment_id": new_assignment.id,
            "next_customer": next_entry.customer.name,
            "next_token": next_entry.token_number
        }

    # 8️⃣ No one waiting
    recalculate_wait_times(restaurant)

    return {
        "message": "Table cleared, no one waiting",
        "table": table.table_number,
        "next_customer": None
    }

def recalculate_wait_times(restaurant):
    waiting_entries = QueueEntry.objects.filter(
        restaurant=restaurant,
        status='waiting',
        expires_at__isnull=True
    ).order_by('joined_at')

    for entry in waiting_entries:
        new_wait = calculate_wait_time(restaurant, entry.party_size, queue_entry=entry)

        # Update only if changed (performance optimization)
        if new_wait != entry.estimated_wait_mins:
            entry.estimated_wait_mins = new_wait
            entry.save(update_fields=['estimated_wait_mins'])


@transaction.atomic
def leave_queue_service(token, restaurant_id):
    # WHAT:
    # → Customer leaves queue before being seated

    # WHY:
    # → Keeps queue clean
    # → Prevents incorrect wait times for others

    try:
        entry = QueueEntry.objects.select_for_update().select_related('restaurant').get(
            token_number=token,
            restaurant_id=restaurant_id,
            status='waiting'
        )
    except QueueEntry.DoesNotExist:
        raise ValueError("No active queue entry found for this token")

    # Mark as left
    entry.status = 'left'
    entry.save(update_fields=['status'])

    # Recalculate wait times for remaining customers
    recalculate_wait_times(entry.restaurant)

    return {
        "message": "You have left the queue",
        "token": token
    }


@transaction.atomic
def call_customer_service(queue_entry_id):
    try:
        entry = QueueEntry.objects.select_for_update().select_related(
            'restaurant',
            'customer'
        ).get(
            id=queue_entry_id,
            status='waiting'
        )
    except QueueEntry.DoesNotExist:
        raise ValueError("Queue entry not found or not waiting")

    table = find_best_table(entry.restaurant, entry.party_size)
    if not table:
        raise ValueError("No available table for this party size")

    assignment = assign_table_and_call_customer(entry, table)
    recalculate_wait_times(entry.restaurant)

    # Send SMS notification
    from notifications.services import notify_table_ready
    try:
        notify_table_ready(entry.id, table.table_number)
    except Exception as e:
        logger.warning(f"Failed to send SMS notification: {str(e)}")

    return {
        "message": "Customer called and table assigned",
        "token": entry.token_number,
        "customer": entry.customer.name,
        "table": table.table_number,
        "assignment_id": assignment.id,
        "expires_at": entry.expires_at,
    }
