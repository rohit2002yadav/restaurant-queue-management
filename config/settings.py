import sys
from datetime import timedelta
from pathlib import Path
from decouple import config

# BASE_DIR points to the root of your project
# Path(__file__) = this file (settings.py)
# .parent = config/ folder
# .parent.parent = project root (new_django_project/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Read SECRET_KEY from .env file — never hardcode this
SECRET_KEY = config('SECRET_KEY')

# Force decouple to read ONLY from .env file, not system env vars for DEBUG
# This prevents system env vars like DEBUG=release from overriding .env
_env_debug = None
if (BASE_DIR / '.env').exists():
    with open(BASE_DIR / '.env') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line.startswith('DEBUG='):
                _env_debug = _line.split('=', 1)[1].strip().lower()
                break

if _env_debug in {'true', '1', 'yes', 'on', 'debug', 'development', 'dev'}:
    DEBUG = True
elif _env_debug in {'false', '0', 'no', 'off', 'release', 'production', 'prod', None}:
    DEBUG = False
else:
    DEBUG = False

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,[::1]',
    cast=lambda value: [host.strip() for host in value.split(',') if host.strip()],
)

# All apps Django needs to know about
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # Django REST Framework — for building APIs
    'corsheaders',

    # Our custom apps
    'accounts',
    'restaurants',
    'queue_manager',
    'orders',
    'notifications',
    'rest_framework_simplejwt.token_blacklist',
    'django_celery_beat',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test.sqlite3',
        }
    }
else:
    db_engine = config('DB_ENGINE', default='mysql').strip().lower()

    if db_engine == 'sqlite':
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
            }
        }
    elif db_engine == 'mysql':
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': config('DB_NAME'),
                'USER': config('DB_USER'),
                'PASSWORD': config('DB_PASSWORD'),
                'HOST': config('DB_HOST', default='localhost'),
                'PORT': config('DB_PORT', default='3306'),
                'OPTIONS': {
                    'charset': 'utf8mb4',
                },
            }
        }
    else:
        raise ValueError("DB_ENGINE must be either 'mysql' or 'sqlite'.")

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'

# IMPORTANT: Use your local timezone
TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

# USE_TZ = True means Django stores all times in UTC in the database
# but displays them in TIME_ZONE (Asia/Kolkata) to users
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon':     '60/minute',
        'user':     '120/minute',
        'otp':      '5/minute',
        'login':    '10/minute',
        'register': '5/minute',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':   timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME':  timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':   True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES':       ('Bearer',),
}

# =========================
# EMAIL CONFIG
# =========================
EMAIL_BACKEND       = config('EMAIL_BACKEND',       default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST          = config('EMAIL_HOST',          default='smtp.gmail.com')
EMAIL_PORT          = config('EMAIL_PORT',          default=587, cast=int)
EMAIL_USE_TLS       = config('EMAIL_USE_TLS',       default='True', cast=lambda v: v.lower() == 'true')
EMAIL_HOST_USER     = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL',  default='Restaurant Queue <noreply@restaurantqueue.com>')

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [o.strip() for o in v.split(',') if o.strip()],
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'origin',
    'x-csrftoken',
    'x-requested-with',
]


# =========================
# CELERY CONFIG
# =========================

CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

CELERY_TIMEZONE = 'Asia/Kolkata'

# =========================
# CELERY BEAT SCHEDULE
# =========================

CELERY_BEAT_SCHEDULE = {
    'check-no-shows-every-minute': {
        'task': 'queue_manager.tasks.check_no_shows',
        'schedule': 60.0,  # every 60 seconds
    },
}

# =========================
# LOGGING CONFIG
# =========================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'celery_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'celery.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'celery_file'],
            'level': config('CELERY_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'queue_manager': {
            'handlers': ['console', 'file'],
            'level': config('APP_LOG_LEVEL', default='DEBUG'),
            'propagate': False,
        },
    },
}

# =========================
# TWILIO SMS CONFIG
# =========================

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')

# Enable/disable SMS sending (useful for testing)
SMS_ENABLED = config('SMS_ENABLED', default='False', cast=lambda v: v.lower() in {'true', '1', 'yes'})

