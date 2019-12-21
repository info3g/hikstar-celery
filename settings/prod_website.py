from .base import *  # noqa

DEBUG = False

SECRET_KEY = "KUhkAATDuMx8evtQyhMkBcGJzQBnhvZj"

ALLOWED_HOSTS = ["hikster.com", "158.69.79.128", "www.hikster.com", "prod.hikster.com"]

EMAIL_USE_SSL = True
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-relay.gmail.com"
EMAIL_PORT = 465
EMAIL_HOST_USER = "contact@hikster.com"
EMAIL_HOST_PASSWORD = "ksl15mltHKC"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

REDIS_URL = "redis://localhost:6379/1"

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Canada/Eastern"

ROOT_URLCONF = "hikster.urls"
LOGIN_URL = "/admin/login/"
MAP_SERVER = "https://hiksterarcgis.goazimut.com/arcgis/rest/services/"
MAP_SERVICE = "Hikster_New_Schema"
ENV = "prod"

THUNDERFOREST_KEY = "5361b27ba5de44d087cc25f5f59e77b4"
