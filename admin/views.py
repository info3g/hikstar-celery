import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers import serialize
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView, TemplateView

from hikster.admin.api.hike.serializers import (
    TrailAdminSerializer,
    TrailSectionAdminSerializer,
    TrailSectionThinSerializer,
    TrailThinSerializer,
)
from hikster.admin.api.location.serializers import (
    LocationAdminSerializer,
    POIAdminSerializer,
    POIAdminThinSerializer,
)
from hikster.hike.models import Activity, Trail, TrailSection
from hikster.location.models import Location
from hikster.location.utils import get_poi_categories
from hikster.organizations.models import Organization
from hikster.organizations.serializers import OrganizationSerializer
from hikster.utils.models import Contact

from .mixins import JsonResponseMixin, OrganizationMixin, POIViewMixin, TrailDetailMixin


class IndexView(LoginRequiredMixin, ListView):
    section = "index"
    model = Organization
    template_name = "hikster-admin/index.html"
    context_object_name = "organizations"

    def get_queryset(self):
        return Organization.objects.filter(members__user=self.request.user)

    def get(self, *args, **kwargs):
        organizations = self.get_queryset()
        if organizations.count() == 1:
            return redirect(
                "hikster-admin:organization", organization_id=organizations.first().id
            )
        return super().get(*args, **kwargs)


class OrganizationView(LoginRequiredMixin, OrganizationMixin, TemplateView):
    section = "profile"
    template_name = "hikster-admin/organization.html"

    def get_loads(self, load_type, years, months):
        return (
            getattr(self.organization, load_type)
            .filter(date_created__year__in=years, date_created__month__in=months)
            .annotate(month=ExtractMonth("date_created"))
            .values("month")
            .annotate(count=Count("pk"))
            .order_by("month")
        )

    def get_loads_data(self):
        def get_value(values, month):
            for item in values:
                if item["month"] == month:
                    return item["count"]
            return 0

        def get_last_months(start_date, number_of_months):
            for i in range(number_of_months):
                yield (start_date.year, start_date.month)
                start_date += relativedelta(months=-1)

        last_5_months = [i for i in get_last_months(timezone.now().date(), 5)]
        years = [i[0] for i in last_5_months]
        months = [i[1] for i in last_5_months]
        page_loads = self.get_loads("page_loads", years, months)
        widget_loads = self.get_loads("widget_loads", years, months)

        loads_data = []
        for item in last_5_months:
            month = datetime.date(item[0], item[1], 1)
            loads_data.append(
                {
                    "month": month,
                    "widget_loads": get_value(widget_loads, item[1]),
                    "page_loads": get_value(page_loads, item[1]),
                }
            )

        return loads_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        org_data = OrganizationSerializer(self.organization).data
        org_data["user"] = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }
        context["organization_data"] = org_data
        context["aid"] = self.organization.aid
        context["loads_data"] = self.get_loads_data()
        return context


class LocationListView(LoginRequiredMixin, OrganizationMixin, TemplateView):
    section = "location-list"
    template_name = "hikster-admin/location-list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        locations = self.organization.locations.all()
        context["default_sport"] = 1
        context["geo_json"] = serialize(
            "geojson",
            locations,
            geometry_field="shape",
            fields=("pk", "location_id", "name"),
        )
        context["map_style"] = "admin-location-list"
        context["poi_categories"] = get_poi_categories()
        context["locations"] = list(
            locations.values("location_id", "name", "modified_date")
        )
        return context


class LocationDetailView(LoginRequiredMixin, OrganizationMixin, DetailView):
    section = "location-detail"
    model = Location
    template_name = "hikster-admin/location-detail.html"
    pk_url_kwarg = "location_id"

    def get_queryset(self):
        return Location.objects.filter(organization=self.organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        location_data = LocationAdminSerializer(self.object).data
        if location_data["address"] is None:
            location_data["address"] = {}
        context["location_data"] = location_data
        context["contact_types_data"] = [
            type_
            for type_ in Contact.TYPE_CHOICES
            if type_[0] in Contact.FRONTEND_TYPES
        ]
        context["location_shape_geojson"] = serialize(
            "geojson",
            self.organization.locations.filter(pk=self.object.pk),
            geometry_field="shape",
            fields=("pk", "location_id", "name"),
        )
        return context


class TrailSectionListView(LoginRequiredMixin, OrganizationMixin, TemplateView):
    section = "trail-sections"
    template_name = "hikster-admin/trail-section-list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trail_sections = self.organization.trail_sections.prefetch_related("activities")
        activities = Activity.objects.values("id", "name").order_by("id")
        context["activities"] = list(activities)
        context["geo_json"] = serialize(
            "geojson",
            trail_sections,
            geometry_field="shape",
            fields=("pk", "trailsection_id", "name"),
        )
        serializer = TrailSectionThinSerializer(trail_sections, many=True)
        context["trail_sections"] = serializer.data
        context["map_style"] = "admin-trail-section-list"
        context["location_geojson"] = serialize(
            "geojson",
            self.organization.locations.all(),
            geometry_field="shape",
            fields=("pk", "location_id", "name"),
        )
        return context


class TrailSectionDetailView(LoginRequiredMixin, OrganizationMixin, DetailView):
    section = "trail-section-detail"
    model = TrailSection
    template_name = "hikster-admin/trail-section-detail.html"
    pk_url_kwarg = "trailsection_id"
    context_object_name = "trail_section"

    def get_queryset(self):
        return self.organization.trail_sections

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trail_section_data = TrailSectionAdminSerializer(self.object).data
        context["trail_section_data"] = trail_section_data
        context["trail_section_shape_geojson"] = serialize(
            "geojson",
            self.organization.trail_sections.filter(pk=self.object.pk),
            geometry_field="shape",
            fields=("pk", "trailsection_id", "name"),
        )
        activities = Activity.objects.values("id", "name").order_by("id")
        context["activities"] = list(activities)
        context["location_geojson"] = serialize(
            "geojson",
            self.organization.locations.all(),
            geometry_field="shape",
            fields=("pk", "location_id", "name"),
        )
        context["other_trail_sections_geojson"] = serialize(
            "geojson",
            self.organization.trail_sections.exclude(pk=self.object.pk),
            geometry_field="shape",
            fields=("pk", "trailsection_id", "name"),
        )
        context["map_style"] = "admin-trail-section-detail"
        return context


class TrailSectionCreateView(LoginRequiredMixin, OrganizationMixin, TemplateView):
    section = "trail-section-detail"
    template_name = "hikster-admin/trail-section-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activities = Activity.objects.values("id", "name").order_by("id")
        context["activities"] = list(activities)
        context["location_geojson"] = serialize(
            "geojson",
            self.organization.locations.all(),
            geometry_field="shape",
            fields=("pk", "location_id", "name"),
        )
        context["other_trail_sections_geojson"] = serialize(
            "geojson",
            self.organization.trail_sections,
            geometry_field="shape",
            fields=("pk", "trailsection_id", "name"),
        )
        context["map_style"] = "admin-trail-section-detail"
        return context


class TrailListView(
    LoginRequiredMixin, OrganizationMixin, JsonResponseMixin, TemplateView
):
    section = "trail-list"
    template_name = "hikster-admin/trail-list.html"

    def get_selected_activity(self):
        activity_id = self.get_query("activity")
        if activity_id is not None:
            activity = get_object_or_404(Activity, id=activity_id)
            return {"id": activity.id, "name": activity.name}
        return {"id": -1, "name": _("All activities")}

    def get_selected_location(self):
        location_id = self.get_query("loc")
        if location_id is not None:
            location = get_object_or_404(
                self.organization.locations, location_id=location_id
            )
            return {"location_id": location_id, "name": location.name}
        return {"location_id": -1, "name": "All locations"}

    def get_trails(self):
        trails = self.organization.trails

        if self.get_query("activity") is not None:
            trails = trails.filter(activities__activity_id=self.get_query("activity"))

        if self.get_query("loc") is not None:
            trails = trails.filter(location_id=self.get_query("loc"))

        return trails

    def get_context_data(self, **kwargs):
        if self.request.is_ajax():
            context = {}
        else:
            context = super().get_context_data(**kwargs)
            activities = Activity.objects.values("id", "name").order_by("id")
            context["activities"] = [{"id": -1, "name": _("All activities")}] + list(
                activities
            )
            context["selected_activity"] = self.get_selected_activity()

            context["locations"] = [
                {"location_id": -1, "name": "All locations"}
            ] + list(
                self.organization.locations.values("location_id", "name").order_by(
                    "name"
                )
            )
            context["selected_location"] = self.get_selected_location()

            context["default_sport"] = self.get_query("activity") or 1
            context["map_style"] = "admin-trail-list"
            context["poi_categories"] = get_poi_categories()

        trails = self.get_trails()
        context["geo_json"] = serialize(
            "geojson",
            trails.filter(shape__isnull=False),
            geometry_field="shape",
            fields=("pk", "trail_id", "name"),
        )
        context["trails"] = TrailThinSerializer(trails, many=True).data
        return context


class TrailCreateView(TrailDetailMixin, TemplateView):
    section = "trail-detail"
    template_name = "hikster-admin/trail-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        return context


class TrailDetailView(TrailDetailMixin, DetailView):
    section = "trail-detail"
    template_name = "hikster-admin/trail-detail.html"
    context_object_name = "trail"
    pk_url_kwarg = "trail_id"

    def get_queryset(self):
        return self.organization.trails

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context["trail_data"] = TrailAdminSerializer(self.object).data
        context["trail_shape_geojson"] = serialize(
            "geojson",
            Trail.objects.filter(pk=self.object.pk),
            geometry_field="shape",
            fields=("pk", "trail_id", "name"),
        )
        context["map_style"] = "admin-trail-detail"
        context["markers"] = self.object.markers
        return context


class POIListView(POIViewMixin, JsonResponseMixin, TemplateView):
    section = "poi-list"
    template_name = "hikster-admin/poi-list.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.poi_categories = get_poi_categories(with_all=True)

    def get_selected_category(self):
        category_id = self.get_query("category")
        if category_id is not None:
            for cat in self.poi_categories:
                if cat["id"] == int(category_id):
                    return cat

        return self.poi_categories[0]

    def get_selected_type(self, category):
        type_id = self.get_query("type")
        if type_id is not None:
            for type_ in category["types"]:
                if type_["id"] == int(type_id):
                    return type_

        return category["types"][0]

    def get_context_data(self, **kwargs):
        if self.request.is_ajax():
            context = {}
        else:
            context = super().get_context_data(**kwargs)
            context["map_style"] = "admin-poi-list"
            selected_category = self.get_selected_category()
            context["selected_category"] = selected_category
            context["selected_type"] = self.get_selected_type(selected_category)
            context["trail_sections_geojson"] = serialize(
                "geojson",
                self.organization.trail_sections,
                geometry_field="shape",
                fields=("pk", "trailsection_id", "name"),
            )
            context["poi_categories"] = self.poi_categories

        context["geo_json"] = serialize(
            "geojson",
            self.get_pois(),
            geometry_field="shape",
            fields=("pk", "name", "type", "display_name"),
        )
        context["point_of_interests"] = POIAdminThinSerializer(
            self.get_pois(), many=True
        ).data

        return context


class POICreateView(POIViewMixin, TemplateView):
    section = "trail-detail"
    template_name = "hikster-admin/poi-detail.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.poi_categories = get_poi_categories()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["map_style"] = "admin-poi-detail"
        context.update(self.get_common_context())
        return context


class POIDetailView(POIViewMixin, DetailView):
    section = "trail-detail"
    template_name = "hikster-admin/poi-detail.html"
    context_object_name = "poi"
    pk_url_kwarg = "poi_id"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.poi_categories = get_poi_categories()

    def get_queryset(self):
        return self.organization.point_of_interests

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["map_style"] = "admin-poi-detail"
        context["poi_data"] = POIAdminSerializer(self.object).data
        context.update(self.get_common_context())
        return context
