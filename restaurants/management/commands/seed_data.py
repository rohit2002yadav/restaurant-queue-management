from django.core.management.base import BaseCommand
from restaurants.models import Restaurant, TableUnit
from orders.models import MenuItem


class Command(BaseCommand):
    help = 'Seed database with a test restaurant, tables, and menu items'

    def handle(self, *args, **kwargs):
        # Create restaurant
        restaurant, created = Restaurant.objects.get_or_create(
            phone='9900000000',
            defaults={
                'name':                   'Spice Garden',
                'address':                '12, MG Road, Bangalore, Karnataka 560001',
                'opening_time':           '09:00',
                'closing_time':           '23:00',
                'avg_meal_duration_mins': 45,
                'max_queue_size':         50,
                'is_active':              True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created restaurant: {restaurant.name} (id={restaurant.id})'))
        else:
            self.stdout.write(f'Restaurant already exists: {restaurant.name} (id={restaurant.id})')

        # Create tables
        tables = [
            ('T1', 2), ('T2', 2),
            ('T3', 4), ('T4', 4), ('T5', 4), ('T6', 4),
            ('T7', 6), ('T8', 6),
        ]
        for table_number, capacity in tables:
            t, c = TableUnit.objects.get_or_create(
                restaurant=restaurant,
                table_number=table_number,
                defaults={'capacity': capacity, 'status': 'available'}
            )
            if c:
                self.stdout.write(f'  Created table {t.table_number} ({t.capacity} seats)')

        # Create menu items
        menu = [
            ('Paneer Butter Masala', 'main',     280, 20, True),
            ('Dal Makhani',          'main',     220, 25, True),
            ('Chicken Biryani',      'main',     350, 30, False),
            ('Butter Naan',          'bread',     40, 10, True),
            ('Garlic Naan',          'bread',     50, 10, True),
            ('Veg Spring Roll',      'starter',  150, 12, True),
            ('Chicken Tikka',        'starter',  280, 15, False),
            ('Gulab Jamun',          'dessert',   80, 5,  True),
            ('Mango Lassi',          'beverage',  90, 5,  True),
            ('Masala Chai',          'beverage',  40, 3,  True),
        ]
        for name, category, price, prep, is_veg in menu:
            m, c = MenuItem.objects.get_or_create(
                restaurant=restaurant,
                name=name,
                defaults={
                    'category':            category,
                    'price':               price,
                    'base_prep_time_mins': prep,
                    'is_veg':              is_veg,
                    'is_available':        True,
                }
            )
            if c:
                self.stdout.write(f'  Created menu item: {m.name}')

        self.stdout.write(self.style.SUCCESS(
            f'\nSeed complete! Restaurant ID = {restaurant.id}\n'
            f'Update RESTAURANT_ID in frontend/src/utils/constants.js to {restaurant.id}'
        ))
