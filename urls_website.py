from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from hikster.core import views_website as core_views
from hikster.hike import views_website as hike_views
from hikster.location import views_website as location_views
from hikster.search import views_website as search_views

from django.views.decorators.clickjacking import xframe_options_exempt

urlpatterns = [
    path("", core_views.HomeView.as_view(), name="home"),
    path("api/", include("hikster.urls_api")),
    path("about/", core_views.AboutView.as_view(), name="about"),
    path("toc/", core_views.TOCView.as_view(), name="toc"),
    path("hikes/<int:pk>/", hike_views.TrailDetailView.as_view(), name="trail-detail"),
    path(
        "locations/<int:pk>/",
        location_views.LocationDetailView.as_view(),
        name="location-detail",
    ),
    path("poi/<int:pk>/", location_views.POIDetailView.as_view(), name="poi-detail"),
    path("results/", search_views.SearchView.as_view(), name="search"),
    path(
        "map-widget/",
        xframe_options_exempt(search_views.SearchViewIframe.as_view()),
        name="search-iframe",
    ),
    path(
        "map-widget/hikes/<int:pk>/",
        xframe_options_exempt(hike_views.TrailDetailView.as_view()),
        name="trail-widget-detail",
    ),
    path(
        "map-widget/locations/<int:pk>/",
        xframe_options_exempt(location_views.LocationDetailView.as_view()),
        name="location-widget-detail",
    ),
    path(
        "map-widget/poi/<int:pk>/",
        xframe_options_exempt(location_views.POIDetailView.as_view()),
        name="poi-widget-detail",
    ),
    path(
        "map-widget/locations/<int:pk>/",
        xframe_options_exempt(location_views.LocationDetailView.as_view()),
        name="location-widget-detail",
    ),
]

if settings.DEBUG:
    urlpatterns = (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
    )
