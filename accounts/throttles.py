from rest_framework.throttling import AnonRateThrottle


class OTPRateThrottle(AnonRateThrottle):
    """5 requests/minute — for OTP verify and resend"""
    scope = 'otp'


class LoginRateThrottle(AnonRateThrottle):
    """10 login attempts/minute per IP"""
    scope = 'login'


class RegisterRateThrottle(AnonRateThrottle):
    """5 registrations/minute per IP"""
    scope = 'register'
