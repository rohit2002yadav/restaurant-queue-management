from rest_framework import serializers
from .models import User


class AdminRegisterSerializer(serializers.Serializer):
    restaurant_name = serializers.CharField(max_length=100)
    name            = serializers.CharField(max_length=100)
    phone           = serializers.CharField(max_length=10)
    email           = serializers.EmailField()
    password        = serializers.CharField(min_length=6, write_only=True)

    def validate_phone(self, value):
        import re
        if not re.match(r'^[6-9]\d{9}$', value):
            raise serializers.ValidationError('Enter a valid 10-digit Indian mobile number')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists')
        return value


class CustomerRegisterSerializer(serializers.Serializer):
    name     = serializers.CharField(max_length=100)
    phone    = serializers.CharField(max_length=10)
    email    = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_phone(self, value):
        import re
        if not re.match(r'^[6-9]\d{9}$', value):
            raise serializers.ValidationError('Enter a valid 10-digit Indian mobile number')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('An account with this email already exists')
        return value


class VerifyOTPSerializer(serializers.Serializer):
    email   = serializers.EmailField()
    otp     = serializers.CharField(min_length=6, max_length=6)
    purpose = serializers.ChoiceField(choices=['registration', 'login'], default='registration')


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ResendOTPSerializer(serializers.Serializer):
    email   = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=['registration', 'login'], default='registration')


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'name', 'phone', 'role', 'restaurant_name', 'restaurant_id', 'is_verified', 'created_at']
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'created_at']
