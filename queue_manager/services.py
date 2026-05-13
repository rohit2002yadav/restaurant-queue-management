from django.utils import timezone
from django.db import transaction
from .models import Customer, QueueEntry, TableAssignment
from restaurants.models import Restaurant, TableUnit



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
    ).order_by('capacity').first()


# =========================================================
# CALCULATE WAIT TIME (IMPROVED LOGIC)
# =========================================================
def calculate_wait_time(restaurant, party_size):

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

    # Count people ahead (excluding expired)
    people_ahead = QueueEntry.objects.filter(
        restaurant=restaurant,
        status='waiting',
        queue_type=queue_type,
        expires_at__isnull=True
    ).count()

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

    # 2️⃣ Get or create customer
    customer, _ = Customer.objects.get_or_create(
        phone=phone,
        defaults={'name': name}
    )

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

        TableAssignment.objects.create(
            queue_entry=queue_entry,
            table_unit=table
        )

        return {
            "message": "Table assigned immediately",
            "token": token,
            "table": table.table_number,
            "wait_time": 0
        }

    # 8️⃣ Otherwise → customer joins queue
    return {
        "message": "Added to queue",
        "token": token,
        "wait_time": wait_time
    }


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

    # 5️⃣ Find next suitable customer (IMPORTANT FIX)
    next_entry = QueueEntry.objects.filter(
        restaurant=restaurant,
        status='waiting',
        expires_at__isnull=True,  # ignore expired users
        party_size__lte=table.capacity
    ).order_by('priority', 'joined_at').first()

    if next_entry:
        # 6️⃣ Assign table
        table.status = 'occupied'
        table.save(update_fields=['status'])

        next_entry.status = 'seated'
        next_entry.seated_at = timezone.now()
        next_entry.save(update_fields=['status', 'seated_at'])

        TableAssignment.objects.create(
            queue_entry=next_entry,
            table_unit=table
        )

        # 7️⃣ Update wait times
        recalculate_wait_times(restaurant)

        return {
            "message": "Table cleared and reassigned",
            "table": table.table_number,
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
        new_wait = calculate_wait_time(restaurant, entry.party_size)

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


