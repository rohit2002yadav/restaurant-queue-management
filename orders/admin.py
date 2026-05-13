from django.contrib import admin
from .models import MenuItem, OrderRecord, OrderItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'category', 'price', 'base_prep_time_mins', 'is_available', 'is_veg']
    list_filter = ['category', 'is_available', 'is_veg', 'restaurant']
    search_fields = ['name']


@admin.register(OrderRecord)
class OrderRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'table_assignment', 'status', 'total_amount', 'placed_at']
    list_filter = ['status']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'order', 'quantity', 'unit_price', 'status']
    list_filter = ['status']
