from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers import serialize
from django.db.models import Case, Q, When
from django.http import Http404, HttpResponseForbidden, JsonResponse

from rest_framework.response import Response

from hikster.hike.models import Activity, Trail
from hikster.hike.utils import graph_edges_nodes
from hikster.organizations.models import Organization
from hikster.utils.models import Contact


class OrganizationMixin:
    section = None

    def __init__(self, *args, **kwargs):
        self.organization = None

        super().__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        try:
            organization = Organization.objects.get(id=kwargs["organization_id"])

        except Organization.DoesNotExist:
            raise Http404()

        try:
            organization.members.get(user=request.user)
        except ObjectDoesNotExist:
            return HttpResponseForbidden()

        self.organization = organization

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["section"] = self.section
        context["organization"] = self.organization

        return context


class TrailDetailMixin(LoginRequiredMixin, OrganizationMixin):
    def get_common_context(self):
        context = {}
        activities = Activity.objects.values("id", "name").order_by("id")
        context["activities"] = list(activities)
        context["map_style"] = "admin-trail-detail"
        context["path_types"] = Trail.PATH_TYPES
        context["locations"] = list(
            self.organization.locations.values("location_id", "name").order_by("name")
        )
        trail_sections = self.organization.trail_sections.prefetch_related("activities")
        context["trail_sections_geojson"] = serialize(
            "geojson",
            trail_sections,
            geometry_field="shape",
            fields=("pk", "trailsection_id", "name"),
        )
        context["graph"] = graph_edges_nodes(trail_sections)
        return context


class JsonResponseMixin(object):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.is_ajax():
            return JsonResponse(context)
        return self.render_to_response(context)

    def get_query(self, key):
        return self.request.GET.get(key, None)


class FileUploadViewMixin(object):
    def _file_upload(self, request, **kwargs):
        serializer = self.get_serializer(
            data=request.data, partial=True, context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        instance = serializer.save(
            credit=request.data.get("credit"),
            image_type=request.data.get("image_type"),
            **kwargs
        )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class POIViewMixin(LoginRequiredMixin, OrganizationMixin):
    poi_categories = []

    def get_query(self, key):
        return self.request.GET.get(key, None)

    def get_pois(self):
        pois = self.organization.point_of_interests.filter(
            visible_in_map=1, category__in=[1, 3, 4, 5, 6]
        )
        if self.get_query("category") is not None:
            pois = pois.filter(category=self.get_query("category"))

        if self.get_query("type") is not None:
            pois = pois.filter(type=self.get_query("type"))

        return pois.annotate(
            display_name=Case(
                When(Q(name__isnull=True) | Q(name=""), then="type__name"),
                default="name",
            )
        )

    def get_common_context(self):
        context = {}
        context["contact_types_data"] = [
            type_
            for type_ in Contact.TYPE_CHOICES
            if type_[0] in Contact.FRONTEND_TYPES
        ]
        context["trail_sections_geojson"] = serialize(
            "geojson",
            self.organization.trail_sections,
            geometry_field="shape",
            fields=("pk", "trailsection_id", "name"),
        )
        other_pois = self.get_pois()
        if hasattr(self, "object"):
            other_pois = other_pois.exclude(pk=self.object.pk)

        context["other_pois_geojson"] = serialize(
            "geojson",
            other_pois,
            geometry_field="shape",
            fields=("pk", "poi_id", "name"),
        )
        context["poi_categories"] = self.poi_categories
        context["location_geojson"] = serialize(
            "geojson",
            self.organization.locations.all(),
            geometry_field="shape",
            fields=("pk",),
        )
        return context
