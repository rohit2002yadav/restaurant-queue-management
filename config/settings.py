from pathlib import Path
from decouple import config

# BASE_DIR points to the root of your project
# Path(__file__) = this file (settings.py)
# .parent = config/ folder
# .parent.parent = project root (new_django_project/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Read SECRET_KEY from .env file — never hardcode this
SECRET_KEY = config('SECRET_KEY')

# Read DEBUG from .env — True in development, False in production
DEBUG = config('DEBUG', cast=bool)

ALLOWED_HOSTS = []

# All apps Django needs to know about
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # Django REST Framework — for building APIs

    # Our custom apps
    'restaurants',
    'queue_manager',
    'orders',
    'notifications',
    'django_celery_beat',
]

MIDDLEWARE = [
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

# Database — reading all values from .env file
# This is why python-decouple is useful
# Your password never appears directly in code
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Use MySQL
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',  # Support emojis in SMS messages
        },
    }
}

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

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}


from celery.schedules import crontab

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