from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import parsers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from hikster.admin.api.filters import TrailIdsFilterSet, TrailSectionIdsFilterSet
from hikster.admin.api.hike.serializers import (
    TrailAdminSerializer,
    TrailImageSerializer,
    TrailSectionAdminSerializer,
)
from hikster.admin.mixins import FileUploadViewMixin
from hikster.hike.models import Activity, Trail, TrailSection, TrailSectionActivity


class TrailSectionAdminViewSet(viewsets.ModelViewSet):
    queryset = TrailSection.objects.all()
    serializer_class = TrailSectionAdminSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterSet

    @action(
        methods=["delete"],
        detail=False,
        url_name="bulk-delete",
        url_path="bulk-delete",
        filterset_class=TrailSectionIdsFilterSet,
    )
    def bulk_delete(self, request):
        self.filter_queryset(self.get_queryset()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post"],
        detail=False,
        url_name="bulk-update",
        url_path="bulk-update",
        filterset_class=TrailSectionIdsFilterSet,
    )
    def bulk_update(self, request):
        activity_ids = request.data.get("activity_ids", "").split(",")
        activities = Activity.objects.filter(id__in=activity_ids)
        data = []
        queryset = self.filter_queryset(self.get_queryset())
        for trail_section in queryset:
            for activity in activities:
                data.append(
                    TrailSectionActivity(trail_section=trail_section, activity=activity)
                )

        with transaction.atomic():
            TrailSectionActivity.objects.filter(trail_section__in=queryset).delete()
            TrailSectionActivity.objects.bulk_create(data)

        return Response(status=status.HTTP_200_OK)


class TrailAdminViewSet(viewsets.ModelViewSet, FileUploadViewMixin):
    queryset = Trail.objects.all()
    serializer_class = TrailAdminSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterSet

    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image",
        parser_classes=(parsers.FormParser, parsers.MultiPartParser),
        serializer_class=TrailImageSerializer,
    )
    def upload_image(self, request, pk=None):
        return self._file_upload(request, trail=self.get_object())

    @action(
        methods=["delete"],
        detail=False,
        url_name="bulk-delete",
        url_path="bulk-delete",
        filterset_class=TrailIdsFilterSet,
    )
    def bulk_delete(self, request):
        self.filter_queryset(self.get_queryset()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def calculate_difficulty_and_duration(self, instance):
        for activity in instance.activities.all():
            activity.calculate_duration()
            activity.calculate_difficulty()
            activity.save()

    def perform_create(self, serializer):
        instance = serializer.save()
        self.calculate_difficulty_and_duration(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.calculate_difficulty_and_duration(instance)
