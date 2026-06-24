from django.test import TestCase
from accounts.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal

from restaurants.models import Restaurant, TableUnit
from queue_manager.models import Customer, QueueEntry, TableAssignment
from .models import MenuItem, OrderRecord, OrderItem
from .services import (
    create_order_service,
    update_order_status_service,
    calculate_estimated_ready_time,
    get_menu_by_restaurant,
)


class MenuItemTestCase(TestCase):
    """Test MenuItem creation and validation"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
        )

    def test_create_menu_items(self):
        item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Burger',
            category='main',
            price=Decimal('250.00'),
            base_prep_time_mins=15,
            is_available=True,
            is_veg=False,
        )
        self.assertEqual(item.name, 'Burger')
        self.assertEqual(item.price, Decimal('250.00'))
        self.assertTrue(item.is_available)

    def test_unavailable_items_filtered(self):
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Burger',
            category='main',
            price=Decimal('250.00'),
            base_prep_time_mins=15,
            is_available=True,
        )
        MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Pasta',
            category='main',
            price=Decimal('300.00'),
            base_prep_time_mins=20,
            is_available=False,
        )

        available = get_menu_by_restaurant(self.restaurant.id)
        self.assertEqual(available.count(), 1)
        self.assertEqual(available.first().name, 'Burger')


class EstimatedReadyTimeTestCase(TestCase):
    """Test prep time calculation"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
        )

    def test_single_item_prep_time(self):
        item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Burger',
            category='main',
            price=Decimal('250.00'),
            base_prep_time_mins=15,
        )

        items_data = [{'menu_item': item, 'quantity': 1}]
        prep_time = calculate_estimated_ready_time(items_data)

        # 15 minutes for 1 burger
        self.assertEqual(prep_time.total_seconds(), 15 * 60)

    def test_multiple_items_same_prep_time(self):
        item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Burger',
            category='main',
            price=Decimal('250.00'),
            base_prep_time_mins=15,
        )

        # 2 burgers: 15 + (2-1)*2 = 17 minutes
        items_data = [{'menu_item': item, 'quantity': 2}]
        prep_time = calculate_estimated_ready_time(items_data)

        self.assertEqual(prep_time.total_seconds(), 17 * 60)

    def test_multiple_different_items(self):
        burger = MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Burger',
            category='main',
            price=Decimal('250.00'),
            base_prep_time_mins=15,
        )
        salad = MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Salad',
            category='starter',
            price=Decimal('150.00'),
            base_prep_time_mins=5,
        )

        # Salad: 5 min, Burger: 15 min → max = 15 min
        items_data = [
            {'menu_item': burger, 'quantity': 1},
            {'menu_item': salad, 'quantity': 1},
        ]
        prep_time = calculate_estimated_ready_time(items_data)

        self.assertEqual(prep_time.total_seconds(), 15 * 60)


class CreateOrderServiceTestCase(TestCase):
    """Test order creation service"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
            avg_meal_duration_mins=45,
        )
        self.table = TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T1',
            capacity=2,
            status='occupied',
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
            status='seated',
        )
        self.assignment = TableAssignment.objects.create(
            queue_entry=self.queue_entry,
            table_unit=self.table,
        )
        self.burger = MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Burger',
            category='main',
            price=Decimal('250.00'),
            base_prep_time_mins=15,
        )

    def test_create_order_successfully(self):
        items_data = [
            {'menu_item_id': self.burger.id, 'quantity': 1, 'special_notes': ''},
        ]

        result = create_order_service(
            table_assignment_id=self.assignment.id,
            items_data=items_data,
            notes='No onions'
        )

        self.assertIn('order_id', result)
        self.assertEqual(result['status'], 'pending')
        self.assertEqual(result['items_count'], 1)

        # Verify order was created
        order = OrderRecord.objects.get(id=result['order_id'])
        self.assertEqual(order.total_amount, Decimal('250.00'))
        self.assertEqual(order.items.count(), 1)

    def test_create_order_with_multiple_items(self):
        pizza = MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Pizza',
            category='main',
            price=Decimal('300.00'),
            base_prep_time_mins=20,
        )

        items_data = [
            {'menu_item_id': self.burger.id, 'quantity': 2, 'special_notes': 'extra spicy'},
            {'menu_item_id': pizza.id, 'quantity': 1, 'special_notes': ''},
        ]

        result = create_order_service(
            table_assignment_id=self.assignment.id,
            items_data=items_data,
        )

        order = OrderRecord.objects.get(id=result['order_id'])
        # 2 * 250 + 1 * 300 = 800
        self.assertEqual(order.total_amount, Decimal('800.00'))
        self.assertEqual(order.items.count(), 2)

    def test_create_order_with_unavailable_item(self):
        self.burger.is_available = False
        self.burger.save()

        items_data = [
            {'menu_item_id': self.burger.id, 'quantity': 1, 'special_notes': ''},
        ]

        with self.assertRaises(ValueError) as context:
            create_order_service(
                table_assignment_id=self.assignment.id,
                items_data=items_data,
            )

        self.assertIn('not found or not available', str(context.exception))

    def test_create_order_with_invalid_table(self):
        items_data = [
            {'menu_item_id': self.burger.id, 'quantity': 1, 'special_notes': ''},
        ]

        with self.assertRaises(ValueError) as context:
            create_order_service(
                table_assignment_id=9999,
                items_data=items_data,
            )

        self.assertIn('not found', str(context.exception))


class UpdateOrderStatusServiceTestCase(TestCase):
    """Test order status updates"""

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
        self.assignment = TableAssignment.objects.create(
            queue_entry=self.queue_entry,
            table_unit=self.table,
        )
        self.order = OrderRecord.objects.create(
            table_assignment=self.assignment,
            status='pending',
        )

    def test_update_order_status(self):
        result = update_order_status_service(self.order.id, 'confirmed')

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')
        self.assertEqual(result['status'], 'confirmed')

    def test_update_order_to_delivered_sets_timestamp(self):
        result = update_order_status_service(self.order.id, 'delivered')

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'delivered')
        self.assertIsNotNone(self.order.delivered_at)

    def test_update_order_invalid_status(self):
        with self.assertRaises(ValueError) as context:
            update_order_status_service(self.order.id, 'invalid_status')

        self.assertIn('Invalid status', str(context.exception))

    def test_update_nonexistent_order(self):
        with self.assertRaises(ValueError) as context:
            update_order_status_service(9999, 'confirmed')

        self.assertIn('not found', str(context.exception))


class OrderAPITestCase(APITestCase):
    """Test Order API endpoints"""

    def setUp(self):
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            phone='9876543210',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
            avg_meal_duration_mins=45,
        )
        self.table = TableUnit.objects.create(
            restaurant=self.restaurant,
            table_number='T1',
            capacity=2,
            status='occupied',
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
            status='seated',
        )
        self.assignment = TableAssignment.objects.create(
            queue_entry=self.queue_entry,
            table_unit=self.table,
        )
        self.burger = MenuItem.objects.create(
            restaurant=self.restaurant,
            name='Burger',
            category='main',
            price=Decimal('250.00'),
            base_prep_time_mins=15,
        )
        self.staff = User.objects.create_superuser(
            email='staff@test.com',
            password='testpass',
            name='Staff User',
            role='admin',
        )
        # Link staff to the test restaurant so ownership checks pass
        self.staff.restaurant_id = self.restaurant.id
        self.staff.save(update_fields=['restaurant_id'])

    def test_get_menu_public(self):
        """Anyone can view menu"""
        response = self.client.get(
            reverse('menu', kwargs={'restaurant_id': self.restaurant.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Burger')

    def test_get_menu_empty_restaurant(self):
        """Menu returns 404 if restaurant has no items"""
        restaurant = Restaurant.objects.create(
            name='Empty Restaurant',
            phone='9876543212',
            address='Test Address',
            opening_time='09:00',
            closing_time='23:00',
        )
        response = self.client.get(
            reverse('menu', kwargs={'restaurant_id': restaurant.id})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_order_requires_auth(self):
        """Unauthenticated request to create order must be rejected"""
        payload = {
            'table_assignment_id': self.assignment.id,
            'items': [
                {'menu_item_id': self.burger.id, 'quantity': 1}
            ],
        }
        response = self.client.post(reverse('create-order'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_success(self):
        """Staff can create order"""
        self.client.force_authenticate(user=self.staff)
        payload = {
            'table_assignment_id': self.assignment.id,
            'items': [
                {'menu_item_id': self.burger.id, 'quantity': 2, 'special_notes': 'extra spicy'}
            ],
            'notes': 'No onions',
        }
        response = self.client.post(reverse('create-order'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_id', response.data)

    def test_update_order_status(self):
        """Staff can update order status"""
        order = OrderRecord.objects.create(
            table_assignment=self.assignment,
            status='pending',
        )
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            reverse('update-order-status', kwargs={'order_id': order.id}),
            {'status': 'confirmed'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, 'confirmed')

    def test_get_table_orders(self):
        """Staff can view all orders for a table"""
        OrderRecord.objects.create(
            table_assignment=self.assignment,
            status='pending',
            total_amount=Decimal('250.00'),
        )
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(
            reverse('table-orders', kwargs={'table_assignment_id': self.assignment.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_active_orders(self):
        """Kitchen staff can view active orders"""
        OrderRecord.objects.create(
            table_assignment=self.assignment,
            status='pending',
        )
        OrderRecord.objects.create(
            table_assignment=self.assignment,
            status='completed',
        )
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(
            reverse('active-orders', kwargs={'restaurant_id': self.restaurant.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only pending order should be returned (not completed)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'pending')

