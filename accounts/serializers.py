import re
from rest_framework import serializers
from .models import User

INDIAN_PHONE_RE = re.compile(r'^[6-9]\d{9}$')


class AdminRegisterSerializer(serializers.Serializer):
    name               = serializers.CharField(max_length=100)
    email              = serializers.EmailField()
    phone              = serializers.CharField(max_length=10)
    password           = serializers.CharField(min_length=6, write_only=True)
    confirm_password   = serializers.CharField(min_length=6, write_only=True)
    restaurant_name    = serializers.CharField(max_length=100)
    restaurant_address = serializers.CharField(max_length=255)

    def validate_phone(self, value):
        if not INDIAN_PHONE_RE.match(value):
            raise serializers.ValidationError('Enter a valid 10-digit Indian mobile number')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists')
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match'})
        return data


class CustomerRegisterSerializer(serializers.Serializer):
    name             = serializers.CharField(max_length=100)
    email            = serializers.EmailField()
    phone            = serializers.CharField(max_length=10)
    password         = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)

    def validate_phone(self, value):
        if not INDIAN_PHONE_RE.match(value):
            raise serializers.ValidationError('Enter a valid 10-digit Indian mobile number')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists')
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match'})
        return data


class VerifyOTPSerializer(serializers.Serializer):
    email   = serializers.EmailField()
    otp     = serializers.CharField(min_length=6, max_length=6)
    purpose = serializers.ChoiceField(choices=['registration', 'login', 'password_reset'], default='registration')


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ResendOTPSerializer(serializers.Serializer):
    email   = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=['registration', 'login', 'password_reset'], default='registration')


class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email            = serializers.EmailField()
    otp              = serializers.CharField(min_length=6, max_length=6)
    new_password     = serializers.CharField(min_length=6, write_only=True)
    confirm_password = serializers.CharField(min_length=6, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match'})
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'name', 'phone', 'role', 'restaurant_name', 'restaurant_phone', 'restaurant_address', 'restaurant_id', 'is_verified', 'created_at']
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'created_at']
