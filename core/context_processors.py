from django.conf import settings as django_settings


def settings(request):
    return {
        "API_URL": django_settings.API_URL,
        "MAP_SERVER": django_settings.MAP_SERVER,
        "MAP_SERVICE": django_settings.MAP_SERVICE,
        "ENV": django_settings.ENV,
        "THUNDERFOREST_KEY": django_settings.THUNDERFOREST_KEY,
    }
