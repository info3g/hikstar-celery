from django.contrib.gis.geos import LineString, MultiLineString
from django.core.serializers import serialize
from django.db.models import Q
from django.templatetags.static import static
from django.views.generic import DetailView

from hikster.core.mixins import PageLoadMixin
from hikster.location.utils import get_poi_categories
from .models import Trail


class TrailDetailView(PageLoadMixin, DetailView):
    model = Trail
    template_name = "website/hike/trail-detail.html"

    def calculate_difficulty_and_duration(self):
        for activity in self.object.activities.filter(
            Q(duration__isnull=True) | Q(difficulty__isnull=True)
        ):
            activity.calculate_duration()
            activity.calculate_difficulty()
            activity.save()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.set_page_load()
        self.calculate_difficulty_and_duration()
        self.object.refresh_from_db()
        context["banner"] = static("img/accueil-1.jpeg")
        banner = self.object.banner
        if banner and banner.image:
            context["banner"] = self.request.build_absolute_uri(banner.image.url)
        context["geo_json"] = serialize(
            "geojson",
            self.model.objects.filter(pk=self.object.pk),
            geometry_field="shape",
        )
        context["map_style"] = "trail"
        context["trail_location"] = {
            "location_id": getattr(self.object.location, "location_id", 0),
            "name": getattr(self.object.location, "name", ""),
        }
        context["poi_categories"] = get_poi_categories()
        context["default_sport"] = 1
        shape = self.object.shape
        if shape:
            if isinstance(shape, LineString):
                lat = shape[0][1]
                lng = shape[0][0]
            elif isinstance(shape, MultiLineString):
                lat = shape[0][0][1]
                lng = shape[0][0][0]
            else:
                center = shape.centroid
                lat = center.y
                lng = center.x

            context["stay22"] = {"lat": lat, "lng": lng}
        return context
