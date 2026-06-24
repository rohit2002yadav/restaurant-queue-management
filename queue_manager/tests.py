from django.urls import reverse
from accounts.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from restaurants.models import Restaurant, TableUnit
from .models import Customer, QueueEntry, TableAssignment
from .services import join_queue_service, recalculate_wait_times
from .tasks import check_no_shows


class QueueWorkflowTests(APITestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
            avg_meal_duration_mins=45,
            max_queue_size=10,
        )
        self.staff_user = User.objects.create_superuser(
            email='staff@example.com',
            password='test-pass',
            name='Staff User',
        )

    def create_customer(self, phone='9876543211', name='Guest'):
        return Customer.objects.create(name=name, phone=phone)

    def join_payload(self, **overrides):
        payload = {
            'restaurant_id': self.restaurant.id,
            'name': 'Rohit',
            'phone': '9876543212',
            'party_size': 2,
            'special_request': '',
        }
        payload.update(overrides)
        return payload

    def test_join_queue_assigns_available_best_fit_table(self):
        TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T4',
            capacity=4,
            status='available',
        )
        TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T2',
            capacity=2,
            status='available',
        )

        response = self.client.post(
            reverse('join-queue'),
            self.join_payload(),
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'seated')
        self.assertEqual(response.data['table'], 'T2')
        self.assertIsNotNone(response.data['assignment_id'])
        self.assertEqual(TableUnit.objects.get(table_number='T2').status, 'occupied')

    def test_join_queue_rejects_duplicate_active_customer(self):
        TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T2',
            capacity=2,
            status='occupied',
        )

        payload = self.join_payload(phone='9876543213')
        first_response = self.client.post(reverse('join-queue'), payload, format='json')
        second_response = self.client.post(reverse('join-queue'), payload, format='json')

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already has an active queue entry', second_response.data['error'])

    def test_queue_status_invalid_token_returns_404(self):
        response = self.client.get(
            reverse('queue-status', kwargs={'token': 'T-999'})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_queue_status_valid_token_returns_correct_structure(self):
        TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T2',
            capacity=2,
            status='occupied',
        )
        entry = join_queue_service(self.join_payload(phone='9876543230'))
        response = self.client.get(
            reverse('queue-status', kwargs={'token': entry['token']})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('queue_entry', response.data)
        self.assertIn('position', response.data)
        self.assertIn('people_ahead', response.data)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['queue_entry']['token_number'], entry['token'])

    def test_queue_status_and_leave_queue(self):
        TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T2',
            capacity=2,
            status='occupied',
        )
        entry = join_queue_service(self.join_payload(phone='9876543214'))

        status_response = self.client.get(
            reverse('queue-status', kwargs={'token': entry['token']})
        )
        leave_response = self.client.post(
            reverse('leave-queue'),
            {'restaurant_id': self.restaurant.id, 'token': entry['token']},
            format='json',
        )

        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(status_response.data['position'], 1)
        self.assertEqual(leave_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            QueueEntry.objects.get(token_number=entry['token']).status,
            'left',
        )

    def test_wait_time_recalculation_excludes_current_entry(self):
        TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T2',
            capacity=2,
            status='occupied',
        )
        first = join_queue_service(self.join_payload(phone='9876543215'))['token']
        second = join_queue_service(self.join_payload(phone='9876543216'))['token']

        recalculate_wait_times(self.restaurant)

        self.assertEqual(
            QueueEntry.objects.get(token_number=first).estimated_wait_mins,
            0,
        )
        self.assertEqual(
            QueueEntry.objects.get(token_number=second).estimated_wait_mins,
            45,
        )

    def test_call_customer_assigns_table_and_creates_no_show_expiry(self):
        table = TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T2',
            capacity=2,
            status='occupied',
        )
        token = join_queue_service(self.join_payload(phone='9876543217'))['token']
        table.status = 'available'
        table.save(update_fields=['status'])

        entry = QueueEntry.objects.get(token_number=token)
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            reverse('call-customer'),
            {'queue_entry_id': entry.id},
            format='json',
        )

        entry.refresh_from_db()
        table.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(entry.status, 'called')
        self.assertIsNotNone(entry.expires_at)
        self.assertEqual(table.status, 'occupied')
        self.assertTrue(TableAssignment.objects.filter(queue_entry=entry, is_active=True).exists())

    def test_clear_table_calls_next_suitable_customer(self):
        active_customer = self.create_customer(phone='9876543218', name='Seated')
        waiting_customer = self.create_customer(phone='9876543219', name='Waiting')
        table = TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T4',
            capacity=4,
            status='occupied',
        )
        active_entry = QueueEntry.objects.create(
            restaurant=self.restaurant,
            customer=active_customer,
            token_number='T-001',
            party_size=2,
            status='seated',
        )
        waiting_entry = QueueEntry.objects.create(
            restaurant=self.restaurant,
            customer=waiting_customer,
            token_number='T-002',
            party_size=4,
            status='waiting',
        )
        assignment = TableAssignment.objects.create(
            queue_entry=active_entry,
            table_unit=table,
        )

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(
            reverse('clear-table'),
            {'table_assignment_id': assignment.id},
            format='json',
        )

        assignment.refresh_from_db()
        active_entry.refresh_from_db()
        waiting_entry.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(assignment.is_active)
        self.assertEqual(active_entry.status, 'completed')
        self.assertEqual(waiting_entry.status, 'called')
        self.assertTrue(
            TableAssignment.objects.filter(
                queue_entry=waiting_entry,
                table_unit=table,
                is_active=True,
            ).exists()
        )

    def test_staff_dashboard_returns_waiting_queue_and_active_tables(self):
        customer = self.create_customer(phone='9876543221', name='Dashboard Guest')
        table = TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T2',
            capacity=2,
            status='occupied',
        )
        seated_entry = QueueEntry.objects.create(
            restaurant=self.restaurant,
            customer=customer,
            token_number='T-001',
            party_size=2,
            status='seated',
        )
        TableAssignment.objects.create(
            queue_entry=seated_entry,
            table_unit=table,
        )
        join_queue_service(self.join_payload(phone='9876543222'))

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(
            reverse('staff-dashboard', kwargs={'restaurant_id': self.restaurant.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['waiting_queue']), 1)
        self.assertEqual(len(response.data['active_tables']), 1)
        self.assertEqual(response.data['active_tables'][0]['table_number'], 'T2')

    def test_check_no_shows_frees_assigned_table(self):
        customer = self.create_customer(phone='9876543220')
        table = TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T2',
            capacity=2,
            status='occupied',
        )
        entry = QueueEntry.objects.create(
            restaurant=self.restaurant,
            customer=customer,
            token_number='T-001',
            party_size=2,
            status='called',
            expires_at=timezone.now() - timezone.timedelta(minutes=1),
        )
        assignment = TableAssignment.objects.create(queue_entry=entry, table_unit=table)

        result = check_no_shows()

        entry.refresh_from_db()
        table.refresh_from_db()
        assignment.refresh_from_db()

        self.assertEqual(result, 'Processed 1 no-show entries')
        self.assertEqual(entry.status, 'no_show')
        self.assertEqual(table.status, 'available')
        self.assertFalse(assignment.is_active)
