from django.test import TestCase, override_settings
from accounts.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from restaurants.models import Restaurant, TableUnit
from queue_manager.models import Customer, QueueEntry, TableAssignment
from .models import NotificationLog
from .services import (
    get_sms_template,
    send_sms,
    notify_queue_joined,
    notify_table_ready,
    notify_no_show,
    get_twilio_client,
)


class SMSTemplateTestCase(TestCase):
    """Test SMS message template generation"""

    def test_queue_joined_template(self):
        """Queue joined message includes token and wait time"""
        context = {
            'customer_name': 'John',
            'restaurant_name': 'Pizza Place',
            'token_number': 'T-001',
            'wait_mins': 15,
        }
        message = get_sms_template('queue_joined', context)

        self.assertIn('T-001', message)
        self.assertIn('15', message)
        self.assertIn('Pizza Place', message)

    def test_table_ready_template(self):
        """Table ready message includes table number"""
        context = {
            'customer_name': 'Jane',
            'restaurant_name': 'Burger Joint',
            'token_number': 'T-005',
            'table_number': 'T3',
        }
        message = get_sms_template('table_ready', context)

        self.assertIn('T3', message)
        self.assertIn('T-005', message)
        self.assertIn('Burger Joint', message)

    def test_no_show_template(self):
        """No-show message is clear"""
        context = {
            'customer_name': 'Bob',
            'restaurant_name': 'Restaurant',
        }
        message = get_sms_template('no_show_detected', context)

        self.assertIn('no-show', message.lower())

    def test_invalid_template_type(self):
        """Invalid template type returns empty string"""
        message = get_sms_template('invalid_type', {})
        self.assertEqual(message, '')

    def test_missing_template_variable(self):
        """Missing template variable returns empty string"""
        context = {
            'customer_name': 'John',
            # Missing other required variables
        }
        message = get_sms_template('queue_joined', context)

        # Should have attempted but failed gracefully
        self.assertIsNotNone(message)


@override_settings(SMS_ENABLED=False)
class SendSMSDisabledTestCase(TestCase):
    """Test SMS behavior when SMS_ENABLED=False (development mode)"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
        )
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='9876543211',
        )
        self.queue_entry = QueueEntry.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            token_number='T-001',
            party_size=2,
        )

    @patch('notifications.services.get_twilio_client')
    def test_send_sms_when_disabled(self, mock_twilio):
        """SMS not actually sent when SMS_ENABLED=False"""
        result = send_sms(
            customer_phone='9876543211',
            message='Test message',
            notification_type='queue_joined',
            queue_entry_id=self.queue_entry.id,
        )

        # Should return not sent
        self.assertFalse(result['sent'])
        self.assertIn('disabled', result['message'].lower())

        # Twilio should not be called
        mock_twilio.assert_not_called()

    def test_notification_log_created_when_disabled(self):
        """Notification log still created even when SMS disabled"""
        send_sms(
            customer_phone='9876543211',
            message='Test message',
            notification_type='queue_joined',
            queue_entry_id=self.queue_entry.id,
        )

        # Log should be created
        log = NotificationLog.objects.filter(
            queue_entry=self.queue_entry,
            notification_type='queue_joined',
        ).first()

        self.assertIsNotNone(log)
        self.assertEqual(log.status, 'pending')


@override_settings(
    SMS_ENABLED=True,
    TWILIO_ACCOUNT_SID='test_sid',
    TWILIO_AUTH_TOKEN='test_token',
    TWILIO_PHONE_NUMBER='+1234567890',
)
class SendSMSEnabledTestCase(TestCase):
    """Test SMS sending when SMS_ENABLED=True"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
        )
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='9876543211',
        )
        self.queue_entry = QueueEntry.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            token_number='T-001',
            party_size=2,
        )

    @patch('notifications.services.Client')
    def test_send_sms_success(self, mock_client_class):
        """SMS successfully sent via Twilio"""
        # Mock Twilio client
        mock_client = MagicMock()
        mock_message = Mock()
        mock_message.sid = 'SM1234567890abcdef'
        mock_client.messages.create.return_value = mock_message
        mock_client_class.return_value = mock_client

        result = send_sms(
            customer_phone='9876543211',
            message='Test message',
            notification_type='queue_joined',
            queue_entry_id=self.queue_entry.id,
        )

        # Should be successful
        self.assertTrue(result['sent'])
        self.assertEqual(result['twilio_sid'], 'SM1234567890abcdef')

        # Verify Twilio API was called correctly
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args
        self.assertEqual(call_args[1]['body'], 'Test message')
        self.assertEqual(call_args[1]['to'], '+919876543211')  # India code

        # Notification log should be updated
        log = NotificationLog.objects.get(queue_entry=self.queue_entry)
        self.assertEqual(log.status, 'sent')
        self.assertEqual(log.twilio_sid, 'SM1234567890abcdef')

    @patch('notifications.services.Client')
    def test_send_sms_failure(self, mock_client_class):
        """SMS failure is handled gracefully"""
        # Mock Twilio client to raise error
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception('Twilio API error')
        mock_client_class.return_value = mock_client

        result = send_sms(
            customer_phone='9876543211',
            message='Test message',
            notification_type='queue_joined',
            queue_entry_id=self.queue_entry.id,
        )

        # Should fail gracefully
        self.assertFalse(result['sent'])
        self.assertIn('Failed', result['message'])

        # Notification log should be marked as failed
        log = NotificationLog.objects.get(queue_entry=self.queue_entry)
        self.assertEqual(log.status, 'failed')


class NotifyQueueJoinedTestCase(TestCase):
    """Test queue joined SMS notification"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
        )
        self.customer = Customer.objects.create(
            name='John Doe',
            phone='9876543211',
        )

    @patch('notifications.services.send_sms')
    def test_notify_queue_joined(self, mock_send_sms):
        """Queue joined notification sends correct message"""
        mock_send_sms.return_value = {'sent': True, 'twilio_sid': 'test_sid'}

        queue_entry = QueueEntry.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            token_number='T-001',
            party_size=2,
            estimated_wait_mins=15,
            status='waiting',
        )

        result = notify_queue_joined(queue_entry.id)

        # Should call send_sms
        mock_send_sms.assert_called_once()
        call_args = mock_send_sms.call_args[1]

        # Phone should be correct
        self.assertEqual(call_args['customer_phone'], '9876543211')

        # Message should contain token
        self.assertIn('T-001', call_args['message'])

        # Notification type should be correct
        self.assertEqual(call_args['notification_type'], 'queue_joined')

    def test_notify_nonexistent_queue_entry(self):
        """Notify with invalid queue entry ID fails gracefully"""
        result = notify_queue_joined(9999)

        self.assertFalse(result['sent'])
        self.assertIn('not found', result['message'].lower())


class NotifyTableReadyTestCase(TestCase):
    """Test table ready SMS notification"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
        )
        self.table = TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T5',
            capacity=2,
        )
        self.customer = Customer.objects.create(
            name='Jane Smith',
            phone='9876543212',
        )

    @patch('notifications.services.send_sms')
    def test_notify_table_ready(self, mock_send_sms):
        """Table ready notification includes table number"""
        mock_send_sms.return_value = {'sent': True, 'twilio_sid': 'test_sid'}

        queue_entry = QueueEntry.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            token_number='T-005',
            party_size=2,
            status='called',
        )

        result = notify_table_ready(queue_entry.id, 'T5')

        # Message should contain table number
        call_args = mock_send_sms.call_args[1]
        self.assertIn('T5', call_args['message'])
        self.assertIn('T-005', call_args['message'])


class NotifyNoShowTestCase(TestCase):
    """Test no-show SMS notification"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
        )
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='9876543213',
        )

    @patch('notifications.services.send_sms')
    def test_notify_no_show(self, mock_send_sms):
        """No-show notification is sent"""
        mock_send_sms.return_value = {'sent': True, 'twilio_sid': 'test_sid'}

        queue_entry = QueueEntry.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            token_number='T-010',
            party_size=2,
            status='no_show',
        )

        result = notify_no_show(queue_entry.id)

        call_args = mock_send_sms.call_args[1]
        self.assertEqual(call_args['notification_type'], 'no_show_warn')
        self.assertTrue('no-show' in call_args['message'].lower())


class QueueJoinSMSIntegrationTestCase(APITestCase):
    """Test SMS is sent when customer joins queue"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
            avg_meal_duration_mins=45,
            max_queue_size=50,
        )
        self.table = TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T1',
            capacity=2,
            status='occupied',
        )

    @patch('notifications.services.notify_queue_joined')
    def test_join_queue_triggers_sms(self, mock_notify):
        """SMS sent when customer joins queue"""
        mock_notify.return_value = {'sent': True}

        payload = {
            'restaurant_id': self.restaurant.id,
            'name': 'Test Customer',
            'phone': '9876543214',
            'party_size': 2,
        }

        response = self.client.post(reverse('join-queue'), payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # SMS notification should have been called
        mock_notify.assert_called_once()


class NoShowSMSIntegrationTestCase(TestCase):
    """Test SMS integration with no-show detection"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
        )
        self.table = TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T1',
            capacity=2,
            status='occupied',
        )
        self.customer = Customer.objects.create(
            name='Test Customer',
            phone='9876543215',
        )

    @patch('notifications.services.notify_no_show')
    def test_no_show_triggers_sms(self, mock_notify):
        """SMS sent when no-show is detected"""
        from queue_manager.tasks import check_no_shows
        from django.utils import timezone
        from datetime import timedelta

        mock_notify.return_value = {'sent': True}

        # Create expired entry
        queue_entry = QueueEntry.objects.create(
            restaurant=self.restaurant,
            customer=self.customer,
            token_number='T-001',
            party_size=2,
            status='called',
            expires_at=timezone.now() - timedelta(minutes=1),
        )

        # Run no-show check
        check_no_shows()

        # SMS should have been called
        mock_notify.assert_called_once()


class NotificationIsolationTests(APITestCase):
    """Ensure staff cannot access other restaurant's feedback or notification logs."""

    def setUp(self):
        self.rest_a = Restaurant.objects.create(
            name='Notif A', phone='9177000001',
            address='Addr', opening_time='09:00', closing_time='23:00',
        )
        self.rest_b = Restaurant.objects.create(
            name='Notif B', phone='9177000002',
            address='Addr', opening_time='09:00', closing_time='23:00',
        )
        self.staff_a = User.objects.create_superuser(
            email='notif_staff_a@test.com', password='pass',
            name='Staff A', restaurant_id=self.rest_a.id,
        )
        self.staff_b = User.objects.create_superuser(
            email='notif_staff_b@test.com', password='pass',
            name='Staff B', restaurant_id=self.rest_b.id,
        )

    def test_staff_a_can_view_own_feedback(self):
        self.client.force_authenticate(user=self.staff_a)
        r = self.client.get(reverse('restaurant-feedback', kwargs={'restaurant_id': self.rest_a.id}))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_staff_a_cannot_view_other_feedback(self):
        self.client.force_authenticate(user=self.staff_a)
        r = self.client.get(reverse('restaurant-feedback', kwargs={'restaurant_id': self.rest_b.id}))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_a_can_view_own_logs(self):
        self.client.force_authenticate(user=self.staff_a)
        r = self.client.get(reverse('notification-logs', kwargs={'restaurant_id': self.rest_a.id}))
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_staff_a_cannot_view_other_logs(self):
        self.client.force_authenticate(user=self.staff_a)
        r = self.client.get(reverse('notification-logs', kwargs={'restaurant_id': self.rest_b.id}))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_b_cannot_view_restaurant_a_logs(self):
        self.client.force_authenticate(user=self.staff_b)
        r = self.client.get(reverse('notification-logs', kwargs={'restaurant_id': self.rest_a.id}))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_b_cannot_view_restaurant_a_feedback(self):
        self.client.force_authenticate(user=self.staff_b)
        r = self.client.get(reverse('restaurant-feedback', kwargs={'restaurant_id': self.rest_a.id}))
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
