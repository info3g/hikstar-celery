from django.contrib.gis.db.models import Extent
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from hikster.hike.models import Activity, Trail, TrailActivity
from hikster.location.models import Location
from hikster.location.utils import get_poi_categories
from hikster.organizations.models import Organization, WidgetLoad


class SearchView(TemplateView):
    template_name = "website/search/result-page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activities = Activity.objects.values("id", "name").order_by("id")
        context["activities"] = list(activities)
        context["types"] = Trail.PATH_TYPES
        context["difficulties"] = TrailActivity.DIFFICULTY_CHOICES
        context["no_footer"] = True
        context["map_style"] = "results"
        context["poi_categories"] = get_poi_categories()
        context["default_sport"] = 1
        context["inner_discovery"] = False

        return context


class SearchViewIframe(TemplateView):

    template_name = "website/search/map-widget.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        params = request.GET
        token, arg_locations = (
            params.get("token"),
            params.get("locations"),
        )

        if arg_locations:
            try:
                location_ids = list(map(int, arg_locations.split(",")))
            except (AttributeError, ValueError):
                context["error_message"] = _("Wrong urls params value")
                return context

        if not token:
            context["error_message"] = _("Unauthorized organization")
            return context

        organization = Organization.objects.filter(aid=token).first()
        if not organization:
            context["error_message"] = _("Invalid organization")
            return context

        if organization.consumed_max_widget_loads:
            context["error_message"] = _(
                "You have exceeded the monthly map load limit."
            )
            return context

        locations = Location.objects.filter(organization=organization)
        if not locations.exists():
            context["error_message"] = _("Organization without location")
            return context

        if arg_locations:
            locations = locations.filter(location_id__in=location_ids)
            if not locations.exists():
                context["error_message"] = _(
                    "These locations do not apply to the organization"
                )
                return context

        widget_load = WidgetLoad.objects.create(
            organization=organization, referrer=request.META.get("HTTP_REFERER", "")
        )

        request.session["widget_org_id"] = organization.pk
        request.session["widget_load_id"] = widget_load.pk
        bounds = locations.aggregate(Extent("shape"))["shape__extent"]

        loc_arg = list(locations.values_list("location_id", flat=True))
        loc_arg = [str(i) for i in loc_arg]
        loc_arg = ",".join(loc_arg)

        context["activities"] = list(
            Activity.objects.values("id", "name").order_by("id")
        )
        context["types"] = Trail.PATH_TYPES
        context["difficulties"] = TrailActivity.DIFFICULTY_CHOICES
        context["map_style"] = "widget"
        context["poi_categories"] = get_poi_categories()
        context["default_sport"] = 1
        context["inner_discovery"] = True
        context["locations"] = loc_arg
        context["bounds"] = {
            "min_lng": bounds[0],
            "min_lat": bounds[1],
            "max_lng": bounds[2],
            "max_lat": bounds[3],
        }

        context["token"] = organization is not None
        return context
