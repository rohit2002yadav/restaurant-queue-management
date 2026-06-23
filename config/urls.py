from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/queue/', include('queue_manager.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/restaurants/', include('restaurants.urls')),
]