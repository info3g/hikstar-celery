from .base import *

DEBUG = True

SECRET_KEY = 'vaFM4JREmeod^3CekEpQTM6Ts7qQjXHm'

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST_USER = "contact@hikster.com"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

REDIS_URL = str(os.environ.get('REDIS_URL'))

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Canada/Eastern'

ROOT_URLCONF = 'hikster.urls_api'
