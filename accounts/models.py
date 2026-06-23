from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('role', 'admin')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('is_verified', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    ROLES = [('admin', 'Admin'), ('customer', 'Customer')]

    email = models.EmailField(unique=True)
    name  = models.CharField(max_length=100)
    phone = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^[6-9]\d{9}$', 'Enter a valid 10-digit Indian mobile number')],
        blank=True
    )
    role        = models.CharField(max_length=10, choices=ROLES, default='customer')
    is_verified = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    # Admin-only: linked restaurant
    restaurant_name = models.CharField(max_length=100, blank=True)
    restaurant_id   = models.IntegerField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return f"{self.email} ({self.role})"


class OTPCode(models.Model):
    email      = models.EmailField()
    code       = models.CharField(max_length=6)
    purpose    = models.CharField(max_length=20, default='registration')  # registration / login
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP {self.code} → {self.email}"
