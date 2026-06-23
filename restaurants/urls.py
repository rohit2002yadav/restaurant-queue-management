from django.urls import path
from .views import RestaurantDetailView

urlpatterns = [
    path('<int:restaurant_id>/', RestaurantDetailView.as_view()),
]
