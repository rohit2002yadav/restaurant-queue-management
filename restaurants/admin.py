from django.contrib import admin
from .models import Restaurant, TableUnit


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'is_active', 'opening_time', 'closing_time']
    # list_display = which columns to show in the list view


@admin.register(TableUnit)
class TableUnitAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'restaurant', 'capacity', 'status', 'is_combinable']
    list_filter = ['status', 'restaurant']
    # list_filter = adds filter sidebar on the right
