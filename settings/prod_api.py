from .base import *

DEBUG = True

SECRET_KEY = 'KUhkAATDuMx8evtQyhMkBcGJzQBnhvZj'

ALLOWED_HOSTS = ['api.prod.hikster.com', '158.69.79.128']

EMAIL_USE_SSL = True
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-relay.gmail.com"
EMAIL_PORT = 465
EMAIL_HOST_USER = "contact@hikster.com"
EMAIL_HOST_PASSWORD = "ksl15mltHKC"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

REDIS_URL = 'redis://localhost:6379/1'

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Canada/Eastern'
