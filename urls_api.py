from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls
from rest_framework_extensions.routers import ExtendedDefaultRouter

from hikster.hike.views import (
    ActivityViewSet,
    EventTrailSectionViewSet,
    EventViewSet,
    Trail3DViewSet,
    TrailSectionViewSet,
    TrailViewSet,
)
from hikster.location.views import LocationViewSet, PointOfInterestViewSet
from hikster.mailing.views import ReservationMailView
from hikster.organizations.views import OrganizationViewSet, ValidateWidgetView
from hikster.search.views import SearchView


trail_routes = ExtendedDefaultRouter()
trail_routes.register(r"trails", TrailViewSet, basename="trail")


trail3d_routes = ExtendedDefaultRouter()
trail3d_routes.register(r"3d-trails", Trail3DViewSet, basename="trail-3d")


location_routes = ExtendedDefaultRouter()

location_routes.register(
    r"locations", LocationViewSet,
    basename="location"
).register(
    r"trails",
    TrailViewSet,
    basename="location-trails",
    parents_query_lookups=["location"],
)


poi_routes = ExtendedDefaultRouter()
poi_routes.register(
    r"point-of-interests", PointOfInterestViewSet, basename="point-of-interests"
)


trailsections_routes = ExtendedDefaultRouter()
trailsections_routes.register(
    r"trailsections", TrailSectionViewSet, basename="trailsections"
)


event_routes = ExtendedDefaultRouter()
event_routes.register(r"events", EventViewSet)


eventtrailsection_routes = ExtendedDefaultRouter()
eventtrailsection_routes.register(r"eventtrailsections", EventTrailSectionViewSet)


org_routes = ExtendedDefaultRouter()
org_routes.register(r"organizations", OrganizationViewSet)

activity_routes = ExtendedDefaultRouter()
activity_routes.register(r"activities", ActivityViewSet)


urlpatterns = [
    url(r"^", include(trail_routes.urls)),
    url(r"^", include(trail3d_routes.urls)),
    url(r"^", include(location_routes.urls)),
    url(r"^", include(poi_routes.urls)),
    url(r"^", include(trailsections_routes.urls)),
    url(r"^", include(event_routes.urls)),
    url(r"^", include(eventtrailsection_routes.urls)),
    url(r"^", include(org_routes.urls)),
    url(r"^", include(activity_routes.urls)),
    url(r"^validate-widget", ValidateWidgetView.as_view()),
    url(r"^search/$", SearchView.as_view()),
    url(r"^reservations/", ReservationMailView.as_view()),
    url(r"^api-auth/", include("rest_framework.urls")),
    url(
        r"^docs/",
        include_docs_urls(
            title="Hikester API",
            authentication_classes=[],
            permission_classes=[],
            public=False,
        ),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
