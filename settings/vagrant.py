from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]

SECRET_KEY = "vaFM4JREmeod^3CekEpQTM6Ts7qQjXHm"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST_USER = "contact@hikster.com"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

REDIS_URL = str(os.environ.get("REDIS_URL"))  # noqa

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Canada/Eastern"

ROOT_URLCONF = "hikster.urls"

LOGIN_URL = "/admin/login/"

WEBPACK_LOADER["DEFAULT"].update(  # noqa
    {
        "BUNDLE_DIR_NAME": "local/dist/",
        "STATS_FILE": os.path.join(BASE_DIR, "webpack-stats-dev.json"),  # noqa
    }
)


MAP_SERVER = "https://hiksterarcgis.goazimut.com/arcgis/rest/services/"
MAP_SERVICE = "Hikster_New_Schema"
