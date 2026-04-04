import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'candidates',
    'frontend',
]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'invision.urls'
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
WSGI_APPLICATION = 'invision.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
_database_url = config('DATABASE_URL', default='')
if _database_url:
    DATABASES['default'] = dj_database_url.parse(_database_url)
DATABASES['bot_db'] = DATABASES['default'].copy()
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Almaty'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    PROJECT_ROOT / 'front',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = True
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
ML_MODEL_PATH = os.path.join(PROJECT_ROOT, 'pipeline', 'models', 'model.pkl')
ML_PIPELINE_DIR = os.path.join(PROJECT_ROOT, 'pipeline')
ML_DATASET_PATH = os.path.join(PROJECT_ROOT, 'data', 'synthetic_dataset.json')
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_CHAT_IDS = config('TELEGRAM_CHAT_IDS', default='', cast=Csv(int))
PANEL_USERNAME = config('PANEL_USERNAME', default='admin')
PANEL_PASSWORD_HASH = config('PANEL_PASSWORD_HASH', default='$2b$12$QwR8Xe2QAdGPZH1Ug2VTGuiiW/UgUCXRYePbVsWPEDDdcdGx3i2f6')
TEACHERS = {
    'teacher1': {
        'name': 'Елена Николаевна',
        'password_hash': '$2b$12$HsFMXLbNtRMUp2Nb80ux3ujTn5spiDW3FSN14OGpk2eDZPbDhO/jq',
    }
}
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} — {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_app': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'file_errors': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'errors.log'),
            'formatter': 'verbose',
            'level': 'ERROR',
            'encoding': 'utf-8',
        },
        'file_applications': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'applications.log'),
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_errors'],
            'level': 'WARNING',
            'propagate': True,
        },
        'candidates': {
            'handlers': ['console', 'file_app', 'file_errors'],
            'level': 'INFO',
            'propagate': False,
        },
        'candidates.applications': {
            'handlers': ['console', 'file_applications'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
