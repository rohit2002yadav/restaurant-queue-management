from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging
from restaurants.models import Restaurant
from .models import QueueEntry, TableAssignment
from .services import (
    recalculate_wait_times,
    get_next_waiting_entry_for_table,
    assign_table_and_call_customer,
)

logger = logging.getLogger(__name__)


# =========================================================
# NO-SHOW CHECK (RUNS EVERY MINUTE)
# =========================================================
@shared_task
def check_no_shows():
    try:
        now = timezone.now()

        expired_entries = QueueEntry.objects.filter(
            status='called',
            expires_at__isnull=False,
            expires_at__lt=now
        ).select_related('restaurant')

        processed = 0
        affected_restaurants = set()

        logger.info(f"Starting no-show check. Found {expired_entries.count()} expired entries.")

        for entry in expired_entries:
            with transaction.atomic():
                entry = QueueEntry.objects.select_for_update().get(id=entry.id)

                if entry.status != 'called':
                    continue

                entry.status = 'no_show'
                entry.save(update_fields=['status'])

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

                    # Auto-call next waiting customer for this table
                    next_entry = get_next_waiting_entry_for_table(entry.restaurant, table)
                    if next_entry:
                        try:
                            assign_table_and_call_customer(next_entry, table)
                            logger.info(
                                f"Auto-called {next_entry.token_number} after no-show "
                                f"{entry.token_number}"
                            )
                        except Exception as call_err:
                            logger.warning(f"Auto-call failed after no-show: {call_err}")

                affected_restaurants.add(entry.restaurant_id)
                processed += 1

                logger.debug(f"Marked no-show: {entry.token_number} at {entry.restaurant.name}")

                try:
                    from notifications.services import notify_no_show
                    notify_no_show(entry.id)
                except Exception as sms_error:
                    logger.warning(f"Failed to send no-show SMS: {str(sms_error)}")

        for restaurant_id in affected_restaurants:
            recalculate_wait_times(Restaurant.objects.get(id=restaurant_id))

        result = f"Processed {processed} no-show entries"
        logger.info(result)
        return result

    except Exception as e:
        error_msg = f"Error in check_no_shows task: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg
