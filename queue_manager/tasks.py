from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .models import QueueEntry, TableAssignment
from .services import recalculate_wait_times


# =========================================================
# NO-SHOW CHECK (RUNS EVERY MINUTE)
# =========================================================
@shared_task
def check_no_shows():
    now = timezone.now()

    expired_entries = QueueEntry.objects.filter(
        status='called',
        expires_at__isnull=False,
        expires_at__lt=now
    ).select_related('restaurant')

    processed = 0
    affected_restaurants = set()

    for entry in expired_entries:
        with transaction.atomic():
            entry = QueueEntry.objects.select_for_update().get(id=entry.id)

            # Skip if already handled
            if entry.status != 'called':
                continue

            # 1️⃣ Mark no-show
            entry.status = 'no_show'
            entry.save(update_fields=['status'])

            # 2️⃣ Free table (lock assignment too)
            assignment = TableAssignment.objects.select_for_update().filter(
                queue_entry=entry,
                is_active=True
            ).select_related('table_unit').first()

            if assignment:
                assignment.cleared_at = now
                assignment.is_active = False
                assignment.save(update_fields=['cleared_at', 'is_active'])

                table = assignment.table_unit
                table.status = 'available'
                table.save(update_fields=['status'])

            affected_restaurants.add(entry.restaurant_id)
            processed += 1

    # 3️⃣ Recalculate once per restaurant (efficient)
    for restaurant_id in affected_restaurants:
        recalculate_wait_times(
            QueueEntry.objects.filter(restaurant_id=restaurant_id).first().restaurant
        )

    return f"Processed {processed} no-show entries"


# =========================================================
# CALL NEXT CUSTOMER
# =========================================================
@shared_task
def call_next_customer(queue_entry_id):
    from datetime import timedelta

    try:
        entry = QueueEntry.objects.select_related('restaurant').get(
            id=queue_entry_id,
            status='waiting'
        )
    except QueueEntry.DoesNotExist:
        return "Entry not found or not waiting"

    now = timezone.now()

    entry.status = 'called'
    entry.called_at = now
    entry.expires_at = now + timedelta(minutes=10)

    entry.save(update_fields=['status', 'called_at', 'expires_at'])

    return f"Called {entry.customer.name} - Token {entry.token_number}"