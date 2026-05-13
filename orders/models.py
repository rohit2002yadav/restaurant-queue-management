from django.db import models
from django.core.validators import MinValueValidator
from restaurants.models import Restaurant
from queue_manager.models import TableAssignment


class MenuItem(models.Model):
    CATEGORY = [
        ('starter', 'Starter'),
        ('main', 'Main Course'),
        ('dessert', 'Dessert'),
        ('beverage', 'Beverage'),
        ('bread', 'Bread'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items'
    )
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY)
    base_prep_time_mins = models.IntegerField(
        validators=[MinValueValidator(1)]
    )
    # How long this dish takes to cook
    # Burger=10, Pizza=20, Salad=5
    # Used to estimate when food will be ready

    price = models.DecimalField(max_digits=8, decimal_places=2)
    # Always DecimalField for money → exact value
    # FloatField has rounding errors → never use for money

    is_available = models.BooleanField(default=True)
    # False → out of stock today

    is_veg = models.BooleanField(default=False)

    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - ₹{self.price}"


class OrderRecord(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
    ]

    table_assignment = models.ForeignKey(
        TableAssignment,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    # One table visit → can have multiple orders
    # Drinks first, then food, then dessert = 3 separate orders

    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    placed_at = models.DateTimeField(auto_now_add=True)
    estimated_ready_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Order #{self.id} - {self.table_assignment}"


class OrderItem(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
    ]

    order = models.ForeignKey(
        OrderRecord,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT
        # PROTECT → can't delete dish that has been ordered before
    )
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    # Snapshot of price at order time
    # If price changes tomorrow, old bills stay correct

    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    special_notes = models.TextField(blank=True)
    # "no onions", "extra spicy"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"
