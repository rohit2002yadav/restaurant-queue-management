from django.contrib import admin
from .models import Customer, QueueEntry, TableAssignment


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'visit_count', 'created_at']
    search_fields = ['name', 'phone']


@admin.register(QueueEntry)
class QueueEntryAdmin(admin.ModelAdmin):
    list_display = ['token_number', 'customer', 'restaurant', 'party_size', 'queue_type', 'status', 'joined_at']
    list_filter = ['status', 'queue_type', 'priority', 'restaurant']
    search_fields = ['token_number', 'customer__name', 'customer__phone']


@admin.register(TableAssignment)
class TableAssignmentAdmin(admin.ModelAdmin):
    list_display = ['queue_entry', 'table_unit', 'assigned_at', 'cleared_at', 'is_active']
    list_filter = ['is_active']
