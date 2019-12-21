from django.contrib.auth import views as auth_views
from django.urls import include, path

from rest_framework import routers


from .api.location import views as location_views
from .api.hike import views as hike_views
from . import views


app_name = "hikster-admin"

router = routers.SimpleRouter()

router.register("locations", location_views.LocationAdminViewSet)
router.register("trail-sections", hike_views.TrailSectionAdminViewSet)
router.register("trails", hike_views.TrailAdminViewSet)
router.register("point-of-interests", location_views.PoiAdminViewSet)


urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="hikster-admin/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="/admin"), name="logout"),
    path(
        "<int:organization_id>/",
        include(
            [
                path("", views.OrganizationView.as_view(), name="organization"),
                path(
                    "locations/", views.LocationListView.as_view(), name="location-list"
                ),
                path(
                    "locations/<int:location_id>/",
                    views.LocationDetailView.as_view(),
                    name="location-detail",
                ),
                path(
                    "trail-sections/",
                    views.TrailSectionListView.as_view(),
                    name="trail-section-list",
                ),
                path(
                    "trail-sections/<int:trailsection_id>/",
                    views.TrailSectionDetailView.as_view(),
                    name="trail-section-detail",
                ),
                path(
                    "trail-sections/new/",
                    views.TrailSectionCreateView.as_view(),
                    name="trail-section-new",
                ),
                path("trails/", views.TrailListView.as_view(), name="trail-list"),
                path(
                    "trails/<int:trail_id>/",
                    views.TrailDetailView.as_view(),
                    name="trail-detail",
                ),
                path("trails/new/", views.TrailCreateView.as_view(), name="trail-new"),
                path("poi/", views.POIListView.as_view(), name="poi-list"),
                path("poi/new/", views.POICreateView.as_view(), name="poi-new"),
                path("poi/<int:poi_id>/", views.POIDetailView.as_view(), name="poi-detail"),
            ]
        ),
    ),
    path("api/", include(router.urls)),
]
