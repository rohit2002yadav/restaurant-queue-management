import logging
from twilio.rest import Client
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import NotificationLog
from queue_manager.models import QueueEntry

logger = logging.getLogger(__name__)


# =========================================================
# TWILIO SMS CLIENT INITIALIZATION
# =========================================================
def get_twilio_client():
    """
    Initialize Twilio client with credentials from settings

    Returns:
        Twilio Client or None if credentials not configured
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials not configured")
        return None

    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


# =========================================================
# SMS MESSAGE TEMPLATES
# =========================================================
def get_sms_template(notification_type, context):
    """
    Generate SMS message based on notification type

    Args:
        notification_type: Type of notification
        context: Dictionary with template variables

    Returns:
        String message ready to send
    """

    templates = {
        'queue_joined': (
            "Hi {customer_name}! You're in the queue at {restaurant_name}. "
            "Your token: {token_number}. Estimated wait: {wait_mins} mins. "
            "Reply LEAVE to leave queue."
        ),
        'two_ahead': (
            "Queue update: 2 parties ahead at {restaurant_name}. "
            "Estimated wait: {wait_mins} mins."
        ),
        'you_are_next': (
            "You're next at {restaurant_name}! Prepare to be seated soon. "
            "Token: {token_number}"
        ),
        'table_ready': (
            "Table ready at {restaurant_name}! Come to table {table_number}. "
            "Token: {token_number}"
        ),
        'no_show_detected': (
            "You were marked as no-show at {restaurant_name}. "
            "If this is a mistake, contact the restaurant."
        ),
        'delay_update': (
            "Delay update at {restaurant_name}: Wait time now {wait_mins} mins. "
            "Token: {token_number}"
        ),
        'order_ready': (
            "Your order is ready at {restaurant_name}! "
            "Total: ₹{total_amount}"
        ),
    }

    template = templates.get(notification_type, "")
    if not template:
        logger.warning(f"Unknown notification type: {notification_type}")
        return ""

    try:
        return template.format(**context)
    except KeyError as e:
        logger.error(f"Missing template variable {e} for {notification_type}")
        return ""


# =========================================================
# SEND SMS VIA TWILIO
# =========================================================
@transaction.atomic
def send_sms(customer_phone, message, notification_type, queue_entry_id=None):
    """
    Send SMS via Twilio and log the attempt

    Args:
        customer_phone: Customer's phone number (10-digit Indian format)
        message: SMS message text
        notification_type: Type of notification (for logging)
        queue_entry_id: Queue entry ID (optional, for linking)

    Returns:
        {
            'sent': bool,
            'twilio_sid': str or None,
            'message': str,
        }
    """

    # Create notification log record (tracks attempt)
    notification_log = None
    queue_entry = None

    if queue_entry_id:
        try:
            queue_entry = QueueEntry.objects.get(id=queue_entry_id)
            notification_log = NotificationLog.objects.create(
                queue_entry=queue_entry,
                notification_type=notification_type,
                channel='sms',
                message=message,
                status='pending',
            )
        except QueueEntry.DoesNotExist:
            logger.error(f"Queue entry {queue_entry_id} not found")
            return {'sent': False, 'twilio_sid': None, 'message': 'Queue entry not found'}

    # Check if SMS is enabled
    if not settings.SMS_ENABLED:
        logger.info(f"SMS disabled. Would send to {customer_phone}: {message}")
        if notification_log:
            notification_log.status = 'pending'
            notification_log.save(update_fields=['status'])
        return {
            'sent': False,
            'twilio_sid': None,
            'message': 'SMS disabled (development mode)',
        }

    # Get Twilio client
    client = get_twilio_client()
    if not client:
        if notification_log:
            notification_log.status = 'failed'
            notification_log.save(update_fields=['status'])
        return {'sent': False, 'twilio_sid': None, 'message': 'Twilio not configured'}

    try:
        # Send SMS
        message_obj = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=f"+91{customer_phone}",  # India country code
        )

        # Update notification log with success
        if notification_log:
            notification_log.status = 'sent'
            notification_log.twilio_sid = message_obj.sid
            notification_log.sent_at = timezone.now()
            notification_log.save(update_fields=['status', 'twilio_sid', 'sent_at'])

        logger.info(f"SMS sent to {customer_phone}: {message_obj.sid}")

        return {
            'sent': True,
            'twilio_sid': message_obj.sid,
            'message': 'SMS sent successfully',
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to send SMS to {customer_phone}: {error_msg}")

        # Update notification log with failure
        if notification_log:
            notification_log.status = 'failed'
            notification_log.save(update_fields=['status'])

        return {
            'sent': False,
            'twilio_sid': None,
            'message': f'Failed to send SMS: {error_msg}',
        }


# =========================================================
# NOTIFY CUSTOMER - Queue Joined
# =========================================================
@transaction.atomic
def notify_queue_joined(queue_entry_id):
    """
    Send SMS when customer joins queue

    Args:
        queue_entry_id: ID of QueueEntry

    Returns:
        Result dict with sent status
    """

    try:
        queue_entry = QueueEntry.objects.select_related(
            'customer', 'restaurant'
        ).get(id=queue_entry_id)
    except QueueEntry.DoesNotExist:
        logger.error(f"Queue entry {queue_entry_id} not found")
        return {'sent': False, 'message': 'Queue entry not found'}

    context = {
        'customer_name': queue_entry.customer.name.split()[0],
        'restaurant_name': queue_entry.restaurant.name,
        'token_number': queue_entry.token_number,
        'wait_mins': queue_entry.estimated_wait_mins,
        'table_number': '',
        'total_amount': '',
    }

    message = get_sms_template('queue_joined', context)

    return send_sms(
        customer_phone=queue_entry.customer.phone,
        message=message,
        notification_type='queue_joined',
        queue_entry_id=queue_entry_id,
    )


# =========================================================
# NOTIFY CUSTOMER - You're Next
# =========================================================
@transaction.atomic
def notify_you_are_next(queue_entry_id):
    """
    Send SMS when customer is about to be called

    Args:
        queue_entry_id: ID of QueueEntry
    """

    try:
        queue_entry = QueueEntry.objects.select_related(
            'customer', 'restaurant'
        ).get(id=queue_entry_id)
    except QueueEntry.DoesNotExist:
        logger.error(f"Queue entry {queue_entry_id} not found")
        return {'sent': False, 'message': 'Queue entry not found'}

    context = {
        'customer_name': queue_entry.customer.name.split()[0],
        'restaurant_name': queue_entry.restaurant.name,
        'token_number': queue_entry.token_number,
    }

    message = get_sms_template('you_are_next', context)

    return send_sms(
        customer_phone=queue_entry.customer.phone,
        message=message,
        notification_type='you_are_next',
        queue_entry_id=queue_entry_id,
    )


# =========================================================
# NOTIFY CUSTOMER - Table Ready (Called)
# =========================================================
@transaction.atomic
def notify_table_ready(queue_entry_id, table_number):
    """
    Send SMS when table is ready and customer is called

    Args:
        queue_entry_id: ID of QueueEntry
        table_number: Table number assigned
    """

    try:
        queue_entry = QueueEntry.objects.select_related(
            'customer', 'restaurant'
        ).get(id=queue_entry_id)
    except QueueEntry.DoesNotExist:
        logger.error(f"Queue entry {queue_entry_id} not found")
        return {'sent': False, 'message': 'Queue entry not found'}

    context = {
        'customer_name': queue_entry.customer.name.split()[0],
        'restaurant_name': queue_entry.restaurant.name,
        'token_number': queue_entry.token_number,
        'table_number': table_number,
    }

    message = get_sms_template('table_ready', context)

    return send_sms(
        customer_phone=queue_entry.customer.phone,
        message=message,
        notification_type='table_ready',
        queue_entry_id=queue_entry_id,
    )


# =========================================================
# NOTIFY CUSTOMER - No-Show Detected
# =========================================================
@transaction.atomic
def notify_no_show(queue_entry_id):
    """
    Send SMS when customer marked as no-show

    Args:
        queue_entry_id: ID of QueueEntry
    """

    try:
        queue_entry = QueueEntry.objects.select_related(
            'customer', 'restaurant'
        ).get(id=queue_entry_id)
    except QueueEntry.DoesNotExist:
        logger.error(f"Queue entry {queue_entry_id} not found")
        return {'sent': False, 'message': 'Queue entry not found'}

    context = {
        'customer_name': queue_entry.customer.name.split()[0],
        'restaurant_name': queue_entry.restaurant.name,
    }

    message = get_sms_template('no_show_detected', context)

    return send_sms(
        customer_phone=queue_entry.customer.phone,
        message=message,
        notification_type='no_show_warn',
        queue_entry_id=queue_entry_id,
    )


# =========================================================
# NOTIFY CUSTOMER - Wait Time Update
# =========================================================
@transaction.atomic
def notify_wait_time_update(queue_entry_id):
    """
    Send SMS when wait time changes significantly

    Args:
        queue_entry_id: ID of QueueEntry
    """

    try:
        queue_entry = QueueEntry.objects.select_related(
            'customer', 'restaurant'
        ).get(id=queue_entry_id)
    except QueueEntry.DoesNotExist:
        logger.error(f"Queue entry {queue_entry_id} not found")
        return {'sent': False, 'message': 'Queue entry not found'}

    context = {
        'customer_name': queue_entry.customer.name.split()[0],
        'restaurant_name': queue_entry.restaurant.name,
        'token_number': queue_entry.token_number,
        'wait_mins': queue_entry.estimated_wait_mins,
    }

    message = get_sms_template('delay_update', context)

    return send_sms(
        customer_phone=queue_entry.customer.phone,
        message=message,
        notification_type='delay_update',
        queue_entry_id=queue_entry_id,
    )


# =========================================================
# CHECK DELIVERY STATUS (Async Task)
# =========================================================
def check_sms_delivery_status(twilio_sid):
    """
    Check SMS delivery status from Twilio

    Args:
        twilio_sid: Twilio message SID

    Returns:
        Message status (queued, sent, delivered, failed, etc.)
    """

    client = get_twilio_client()
    if not client:
        return 'unknown'

    try:
        message = client.messages(twilio_sid).fetch()
        return message.status
    except Exception as e:
        logger.error(f"Failed to check SMS status {twilio_sid}: {str(e)}")
        return 'unknown'
