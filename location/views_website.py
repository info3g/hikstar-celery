from collections import defaultdict

from django.core.serializers import serialize
from django.templatetags.static import static
from django.views.generic import DetailView

from hikster.admin.api.location.serializers import POIAdminSerializer
from hikster.core.mixins import PageLoadMixin
from hikster.utils.helpers import is_email, is_url

from .models import Location, PointOfInterest
from .utils import get_poi_categories


class ContactMixin(object):
    def _get_contacts(self):
        contacts = defaultdict(list)
        for contact in self.object.contact.values_list("value", flat=True):
            if is_email(contact):
                contacts["emails"].append(contact)
            elif is_url(contact):
                contacts["websites"].append(contact)
            else:
                contacts["phones"].append(contact)

        return contacts


class LocationDetailView(PageLoadMixin, ContactMixin, DetailView):
    model = Location
    template_name = "website/location/location-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.set_page_load()
        context["banner"] = static("img/accueil-1.jpeg")
        banner = self.object.images.banners().first()
        if banner and banner.image:
            context["banner"] = self.request.build_absolute_uri(banner.image.url)

        context["contacts"] = self._get_contacts()
        context["geo_json"] = serialize(
            "geojson",
            self.model.objects.filter(pk=self.object.pk),
            geometry_field="shape",
        )
        context["trails_json"] = serialize(
            "geojson", self.object.trails.all(), geometry_field="shape"
        )
        context["map_style"] = "location"
        context["poi_categories"] = get_poi_categories()
        context["default_sport"] = self.request.GET.get("sport", 1)
        if self.object.shape:
            center = self.object.shape.centroid
            context["stay22"] = {"lat": center.y, "lng": center.x}
        return context


class POIDetailView(PageLoadMixin, ContactMixin, DetailView):
    model = PointOfInterest
    template_name = "website/location/poi-detail.html"
    context_object_name = "poi"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.set_page_load()
        context["banner"] = static("img/accueil-1.jpeg")
        banner = self.object.images.banners().first()
        if banner and banner.image:
            context["banner"] = self.request.build_absolute_uri(banner.image.url)

        context["contacts"] = self._get_contacts()
        context["map_style"] = "poi"
        context["default_sport"] = self.request.GET.get("sport", 1)
        context["poi_json"] = POIAdminSerializer(self.object).data
        return context
