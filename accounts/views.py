import logging
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import (
    AdminRegisterSerializer,
    CustomerRegisterSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    ResendOTPSerializer,
    UserProfileSerializer,
    RequestPasswordResetSerializer,
    ResetPasswordSerializer,
)
from .services import create_otp, send_otp_email, verify_otp, get_tokens_for_user
from .throttles import OTPRateThrottle, LoginRateThrottle, RegisterRateThrottle

logger = logging.getLogger(__name__)


@transaction.atomic
def _create_restaurant_for_admin(user):
    """Create a Restaurant + default tables for a newly verified admin."""
    from restaurants.models import Restaurant

    # Idempotent: return early if already linked
    if user.restaurant_id:
        return user.restaurant_id

    # Check by phone (unique constraint) to avoid IntegrityError on retry
    existing = Restaurant.objects.filter(phone=user.phone).first()
    if existing:
        return existing.id

    restaurant = Restaurant.objects.create(
        name                   = user.restaurant_name,
        phone                  = user.phone,
        address                = user.restaurant_address or 'Please update your address',
        opening_time           = '09:00',
        closing_time           = '23:00',
        avg_meal_duration_mins = 45,
        max_queue_size         = 50,
        is_active              = True,
    )

    logger.info(f"Created restaurant '{restaurant.name}' (id={restaurant.id}) for admin {user.email}")
    return restaurant.id


def _otp_response(message, email, otp):
    """Build response — include otp only in DEBUG mode for easy testing."""
    data = {'message': message, 'email': email}
    if settings.DEBUG:
        data['dev_otp'] = otp
    return data


class AdminRegisterView(APIView):
    throttle_classes = [RegisterRateThrottle]
    def post(self, request):
        serializer = AdminRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email              = data['email'],
                    password           = data['password'],
                    name               = data['name'],
                    phone              = data['phone'],
                    role               = 'admin',
                    restaurant_name    = data['restaurant_name'],
                    restaurant_address = data['restaurant_address'],
                    is_verified        = False,
                )
            otp  = create_otp(data['email'], purpose='registration')
            send_otp_email(data['email'], otp, purpose='registration')
            return Response(_otp_response(
                'OTP sent to your email. Please verify to complete registration.',
                data['email'], otp
            ), status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Admin register error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerRegisterView(APIView):
    throttle_classes = [RegisterRateThrottle]
    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email       = data['email'],
                    password    = data['password'],
                    name        = data['name'],
                    phone       = data['phone'],
                    role        = 'customer',
                    is_verified = False,
                )
            otp  = create_otp(data['email'], purpose='registration')
            send_otp_email(data['email'], otp, purpose='registration')
            return Response(_otp_response(
                'OTP sent to your email. Please verify to complete registration.',
                data['email'], otp
            ), status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Customer register error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(APIView):
    throttle_classes = [OTPRateThrottle]
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data    = serializer.validated_data
        email   = data['email']
        otp     = data['otp']
        purpose = data['purpose']

        valid, message = verify_otp(email, otp, purpose=purpose)
        if not valid:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        if purpose == 'registration':
            try:
                user = User.objects.get(email=email, is_verified=False)
                user.is_verified = True
                user.save(update_fields=['is_verified'])
            except User.DoesNotExist:
                return Response({'error': 'User not found or already verified'}, status=status.HTTP_400_BAD_REQUEST)

            # Auto-create restaurant + tables for admin
            restaurant_id = None
            if user.role == 'admin':
                with transaction.atomic():
                    restaurant_id = _create_restaurant_for_admin(user)
                    user.restaurant_id = restaurant_id
                    user.save(update_fields=['restaurant_id'])

            return Response({
                'message': 'Email verified successfully. You can now log in.',
                'role': user.role,
                'restaurant_id': restaurant_id,
            }, status=status.HTTP_200_OK)

        # purpose == 'login'
        try:
            user = User.objects.get(email=email, is_verified=True)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)

        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Login successful',
            'tokens': tokens,
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_200_OK)


class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(data['password']):
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_verified:
            return Response({
                'error': 'Email not verified. Please verify your email first.',
                'email': user.email,
                'needs_verification': True,
            }, status=status.HTTP_403_FORBIDDEN)

        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Login successful',
            'tokens': tokens,
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    throttle_classes = [OTPRateThrottle]
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email   = serializer.validated_data['email']
        purpose = serializer.validated_data['purpose']

        if not User.objects.filter(email=email).exists():
            # Return 200 instead of 404 to prevent account enumeration
            return Response({'message': 'If an account exists, OTP has been resent'}, status=status.HTTP_200_OK)

        otp  = create_otp(email, purpose=purpose)
        send_otp_email(email, otp, purpose=purpose)

        return Response({
            'message': 'OTP resent successfully',
            **({"dev_otp": otp} if settings.DEBUG else {}),
        }, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)


class RequestPasswordResetView(APIView):
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        # Always return 200 to prevent account enumeration
        if User.objects.filter(email=email, is_verified=True).exists():
            otp = create_otp(email, purpose='password_reset')
            send_otp_email(email, otp, purpose='password_reset')
            data = {'message': 'If an account exists, a reset OTP has been sent'}
            if settings.DEBUG:
                data['dev_otp'] = otp
            return Response(data, status=status.HTTP_200_OK)

        return Response({'message': 'If an account exists, a reset OTP has been sent'}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        valid, message = verify_otp(data['email'], data['otp'], purpose='password_reset')
        if not valid:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=data['email'], is_verified=True)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(data['new_password'])
        user.save(update_fields=['password'])
        return Response({'message': 'Password reset successful. You can now log in.'}, status=status.HTTP_200_OK)
