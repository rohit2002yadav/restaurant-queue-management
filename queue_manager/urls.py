from django.urls import path
from .views import (
    JoinQueueView,
    QueueStatusView,
    RestaurantQueueView,
    StaffDashboardView,
    ClearTableView,
    LeaveQueueView,
    CallCustomerView,
    SeatCustomerView,
    MyActiveQueueView,
)

urlpatterns = [
    path('join-queue/',                        JoinQueueView.as_view(),         name='join-queue'),
    path('queue-status/<str:token>/',          QueueStatusView.as_view(),       name='queue-status'),
    path('restaurant-queue/<int:restaurant_id>/', RestaurantQueueView.as_view(), name='restaurant-queue'),
    path('staff-dashboard/<int:restaurant_id>/',  StaffDashboardView.as_view(),  name='staff-dashboard'),
    path('clear-table/',                       ClearTableView.as_view(),        name='clear-table'),
    path('leave-queue/',                       LeaveQueueView.as_view(),        name='leave-queue'),
    path('call-customer/',                     CallCustomerView.as_view(),      name='call-customer'),
    path('seat-customer/',                     SeatCustomerView.as_view(),      name='seat-customer'),
    path('my-active-queue/',                   MyActiveQueueView.as_view(),     name='my-active-queue'),
]
