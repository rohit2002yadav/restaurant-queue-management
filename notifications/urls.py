from django.urls import path
from .views import SubmitFeedbackView, RestaurantFeedbackView, NotificationLogsView

urlpatterns = [
    path('feedback/', SubmitFeedbackView.as_view(), name='submit-feedback'),
    path('feedback/restaurant/<int:restaurant_id>/', RestaurantFeedbackView.as_view(), name='restaurant-feedback'),
    path('logs/<int:restaurant_id>/', NotificationLogsView.as_view(), name='notification-logs'),
]
