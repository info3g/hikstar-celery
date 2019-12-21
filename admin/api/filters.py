from django_filters.constants import EMPTY_VALUES
from django_filters.rest_framework import BaseInFilter, FilterSet, NumberFilter

from hikster.hike.models import Trail, TrailSection
from hikster.location.models import PointOfInterest


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class NumberInOrEmptyFilter(BaseInFilter, NumberFilter):
    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs.none()

        return super().filter(qs, value)


class TrailSectionIdsFilterSet(FilterSet):
    ids = NumberInOrEmptyFilter(field_name="trailsection_id", lookup_expr="in")

    class Meta:
        model = TrailSection
        fields = ["trailsection_id"]


class TrailIdsFilterSet(FilterSet):
    ids = NumberInOrEmptyFilter(field_name="trail_id", lookup_expr="in")

    class Meta:
        model = Trail
        fields = ["trail_id"]


class PoiIdsFilterSet(FilterSet):
    ids = NumberInOrEmptyFilter(field_name="poi_id", lookup_expr="in")

    class Meta:
        model = PointOfInterest
        fields = ["poi_id"]
