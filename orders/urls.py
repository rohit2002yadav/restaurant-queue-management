from django.urls import path
from .views import (
    MenuView,
    CreateOrderView,
    OrderDetailView,
    UpdateOrderStatusView,
    UpdateOrderItemStatusView,
    TableOrdersView,
    RestaurantActiveOrdersView,
)

urlpatterns = [
    # ========== Public Endpoints ==========
    # Get menu for a restaurant (public - no auth required)
    path('menu/<int:restaurant_id>/', MenuView.as_view(), name='menu'),

    # ========== Staff Endpoints (Requires Admin Auth) ==========
    # Create new order
    path('create/', CreateOrderView.as_view(), name='create-order'),

    # Get order details
    path('<int:order_id>/', OrderDetailView.as_view(), name='order-detail'),

    # Update order status
    path('<int:order_id>/status/', UpdateOrderStatusView.as_view(), name='update-order-status'),

    # Update individual item status
    path('item/<int:item_id>/status/', UpdateOrderItemStatusView.as_view(), name='update-item-status'),

    # Get all orders for a specific table
    path('table/<int:table_assignment_id>/', TableOrdersView.as_view(), name='table-orders'),

    # Get active orders for restaurant (kitchen dashboard)
    path('restaurant/<int:restaurant_id>/active/', RestaurantActiveOrdersView.as_view(), name='active-orders'),
]
