from django.urls import path
from .views import (
    JoinQueueView,
    QueueStatusView,
    RestaurantQueueView,
    StaffDashboardView,
    ClearTableView,
    LeaveQueueView,
    CallCustomerView
)

urlpatterns = [
    # Customer joins queue
    path('join-queue/', JoinQueueView.as_view(), name='join-queue'),

    # Customer checks status
    path('queue-status/<str:token>/', QueueStatusView.as_view(), name='queue-status'),

    # Staff views queue
    path('restaurant-queue/<int:restaurant_id>/', RestaurantQueueView.as_view(), name='restaurant-queue'),

    # Staff dashboard data
    path('staff-dashboard/<int:restaurant_id>/', StaffDashboardView.as_view(), name='staff-dashboard'),

    # Staff clears table
    path('clear-table/', ClearTableView.as_view(), name='clear-table'),

    # Customer leaves queue
    path('leave-queue/', LeaveQueueView.as_view(), name='leave-queue'),

    # 🔥 Staff calls customer
    path('call-customer/', CallCustomerView.as_view(), name='call-customer'),
]
