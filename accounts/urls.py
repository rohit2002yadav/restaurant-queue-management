from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    AdminRegisterView,
    CustomerRegisterView,
    VerifyOTPView,
    LoginView,
    ResendOTPView,
    ProfileView,
)

urlpatterns = [
    path('admin/register/',    AdminRegisterView.as_view(),    name='admin-register'),
    path('customer/register/', CustomerRegisterView.as_view(), name='customer-register'),
    path('verify-otp/',        VerifyOTPView.as_view(),        name='verify-otp'),
    path('login/',             LoginView.as_view(),            name='login'),
    path('resend-otp/',        ResendOTPView.as_view(),        name='resend-otp'),
    path('token/refresh/',     TokenRefreshView.as_view(),     name='token-refresh'),
    path('profile/',           ProfileView.as_view(),          name='profile'),
]
