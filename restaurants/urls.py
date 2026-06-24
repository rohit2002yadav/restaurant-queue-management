from django.urls import path
from .views import RestaurantListView, RestaurantDetailView

urlpatterns = [
    path('', RestaurantListView.as_view(), name='restaurant-list'),
    path('<int:restaurant_id>/', RestaurantDetailView.as_view(), name='restaurant-detail'),
]
