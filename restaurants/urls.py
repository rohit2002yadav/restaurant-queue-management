from django.urls import path
from .views import (
    RestaurantListView,
    RestaurantDetailView,
    TableListView,
    TableBulkCreateView,
    TableDetailView,
)

urlpatterns = [
    path('',                                    RestaurantListView.as_view(),      name='restaurant-list'),
    path('<int:restaurant_id>/',                RestaurantDetailView.as_view(),    name='restaurant-detail'),
    path('<int:restaurant_id>/tables/',         TableListView.as_view(),           name='table-list'),
    path('<int:restaurant_id>/tables/bulk-create/', TableBulkCreateView.as_view(), name='table-bulk-create'),
    path('tables/<int:table_id>/',              TableDetailView.as_view(),         name='table-detail'),
]
