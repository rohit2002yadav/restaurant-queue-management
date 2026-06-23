import random
import logging
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, OTPCode

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 10


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp, purpose='registration'):
    subject = 'Your OTP — Restaurant Queue System'
    if purpose == 'registration':
        body = (
            f"Welcome to Restaurant Queue System!\n\n"
            f"Your email verification OTP is: {otp}\n\n"
            f"This OTP is valid for {OTP_EXPIRY_MINUTES} minutes.\n"
            f"Do not share this with anyone."
        )
    else:
        body = (
            f"Your login OTP is: {otp}\n\n"
            f"Valid for {OTP_EXPIRY_MINUTES} minutes."
        )

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"OTP email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {e}")
        return False


@transaction.atomic
def create_otp(email, purpose='registration'):
    # Invalidate old unused OTPs for this email+purpose
    OTPCode.objects.filter(email=email, purpose=purpose, is_used=False).update(is_used=True)

    otp = generate_otp()
    OTPCode.objects.create(email=email, code=otp, purpose=purpose)
    return otp


def verify_otp(email, code, purpose='registration'):
    expiry_threshold = timezone.now() - timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp_obj = OTPCode.objects.filter(
        email=email,
        code=code,
        purpose=purpose,
        is_used=False,
        created_at__gte=expiry_threshold
    ).order_by('-created_at').first()

    if not otp_obj:
        return False, 'Invalid or expired OTP'

    otp_obj.is_used = True
    otp_obj.save(update_fields=['is_used'])
    return True, 'OK'


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['role']          = user.role
    refresh['name']          = user.name
    refresh['email']         = user.email
    refresh['restaurant_id'] = user.restaurant_id
    return {
        'refresh': str(refresh),
        'access':  str(refresh.access_token),
    }
