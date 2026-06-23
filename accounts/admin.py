from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['email', 'name', 'role', 'is_verified', 'is_active', 'created_at']
    list_filter   = ['role', 'is_verified', 'is_active']
    search_fields = ['email', 'name', 'phone']
    ordering      = ['-created_at']

    fieldsets = (
        (None,           {'fields': ('email', 'password')}),
        ('Personal',     {'fields': ('name', 'phone', 'restaurant_name')}),
        ('Permissions',  {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'name', 'phone', 'role', 'password1', 'password2')}),
    )


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ['email', 'code', 'purpose', 'is_used', 'created_at']
    list_filter  = ['purpose', 'is_used']
