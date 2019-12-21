from django.contrib.gis import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path


urlpatterns = [
    path("", include("hikster.urls_website")),
    path("django-admin/", admin.site.urls),
    path("django-admin/rq/", include("django_rq.urls")),
    path("admin/", include("hikster.admin.urls")),
]

if settings.DEBUG:
    urlpatterns = (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
    )
