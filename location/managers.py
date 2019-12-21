from django.db import models


class LocationManager(models.Manager):
    def get_queryset(self):
        queryset = super(LocationManager, self).get_queryset()
        queryset = queryset.select_related("address")
        return queryset


class PointOfInterestManager(models.Manager):
    def get_queryset(self):
        queryset = super(PointOfInterestManager, self).get_queryset()
        queryset = queryset.select_related("address", "type")
        return queryset
