from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """Allow access only to users with role='admin'."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'admin'
        )


class IsCustomerRole(BasePermission):
    """Allow access only to users with role='customer'."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'customer'
        )
