from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from rest_framework import parsers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from hikster.admin.api.filters import PoiIdsFilterSet
from hikster.admin.api.location.serializers import (
    LocationAdminSerializer,
    LocationImageSerializer,
    POIAdminSerializer,
    POIImageSerializer,
)
from hikster.admin.mixins import FileUploadViewMixin
from hikster.location.models import Location, PointOfInterest


class LocationAdminViewSet(viewsets.ModelViewSet, FileUploadViewMixin):
    queryset = Location.objects.all()
    serializer_class = LocationAdminSerializer

    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image",
        parser_classes=(parsers.FormParser, parsers.MultiPartParser),
        serializer_class=LocationImageSerializer,
    )
    def upload_image(self, request, pk=None):
        return self._file_upload(request, location=self.get_object())


class PoiAdminViewSet(viewsets.ModelViewSet, FileUploadViewMixin):
    queryset = PointOfInterest.objects.all()
    serializer_class = POIAdminSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterSet

    @action(
        methods=["post"],
        detail=True,
        url_path="upload-image",
        parser_classes=(parsers.FormParser, parsers.MultiPartParser),
        serializer_class=POIImageSerializer,
    )
    def upload_image(self, request, pk=None):
        return self._file_upload(request, location=self.get_object())

    @action(
        methods=["delete"],
        detail=False,
        url_name="bulk-delete",
        url_path="bulk-delete",
        filterset_class=PoiIdsFilterSet,
    )
    def bulk_delete(self, request):
        self.filter_queryset(self.get_queryset()).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
