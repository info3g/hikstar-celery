import os

from django.utils.translation import ugettext_lazy as _

from . import secrets

PROJECT_DIR = secrets.APP_INSTALL_DIR
BASE_DIR = os.path.join(PROJECT_DIR, "src")
VAR_DIR = os.path.join(PROJECT_DIR, "var")
XAPIAN_PATH = os.path.join(secrets.XAPIAN_PATH, "var", "xapian_index")

SITE_ID = 1
DEBUG = False

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.sites",
    "django.contrib.postgres",
    # Plugins
    "corsheaders",
    "django_filters",
    "django_rq",
    "easy_thumbnails",
    "haystack",
    "rest_framework",
    "rest_framework_gis",
    "webpack_loader",
    "widget_tweaks",
    # Project app
    "hikster.core",
    "hikster.hike",
    "hikster.location",
    "hikster.organizations",
    "hikster.search.apps.SearchConfig",
    "hikster.utils",
]

CORS_ORIGIN_ALLOW_ALL = True

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": secrets.APP_DATABASE,
        "USER": secrets.APP_DATABASE_USER,
        "PASSWORD": secrets.APP_DATABASE_PASSWORD,
        "HOST": "localhost",
        "PORT": "5432",
    }
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly"
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.AcceptHeaderVersioning",
    "DEFAULT_VERSION": "2.0",
    "ALLOWED_VERSIONS": ("2.0"),
}

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "hikster.core.middleware.WidgetMiddleware",
]

ROOT_URLCONF = "hikster.urls_api"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "hikster/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "hikster.core.context_processors.settings",
            ]
        },
    }
]

WSGI_APPLICATION = "hikster.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = "fr"
LANGUAGES = [("en", _("English")), ("fr", _("French"))]

TIME_ZONE = "UTC"

USE_I18N = True
USE_L10N = True
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

USE_TZ = True

REST_SESSION_LOGIN = False
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
REST_USE_JWT = True

OLD_PASSWORD_FIELD_ENABLED = False
LOGOUT_ON_PASSWORD_CHANGE = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(PROJECT_DIR, "public/static")
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(PROJECT_DIR, "public/media")
MEDIA_URL = "/media/"

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (os.path.join(BASE_DIR, "hikster/static"),)

ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200

HAYSTACK_CONNECTIONS = {
    "default": {"ENGINE": "xapian_backend.XapianEngine", "PATH": XAPIAN_PATH}
}

IPSTACK_KEY = "4b6828d320d839eefb2f1e1a08dd5f51"

THUMBNAIL_ALIASES = {"": {"standard": {"size": (2048, 1536), "crop": True}}}

WEBPACK_LOADER = {
    "DEFAULT": {
        "BUNDLE_DIR_NAME": "dist/",
        "STATS_FILE": os.path.join(BASE_DIR, "webpack-stats.json"),
        "CACHE": not DEBUG,
    }
}

if DEBUG:
    WEBPACK_LOADER["DEFAULT"].update(
        {
            "BUNDLE_DIR_NAME": "local/dist/",
            "STATS_FILE": os.path.join(BASE_DIR, "webpack-stats-dev.json"),
        }
    )

CSRF_COOKIE_NAME = "XSRF-TOKEN"
API_URL = None
MAP_SERVER = "https://hiksterarcgis.goazimut.com/arcgis/rest/services/"
MAP_SERVICE = "Hikster_New_Schema"
ENV = "dev"

RQ_QUEUES = {
    "default": {"HOST": "localhost", "PORT": 6379, "DB": 0, "DEFAULT_TIMEOUT": 360}
}

SESSION_COOKIE_SAMESITE = None

# default key for dev
THUNDERFOREST_KEY = "9808d4cd9b8049efaa10f74e075afb89"
