from django.db import models


# Custom manager to return objects eagerly. This is to prevent overriding get_queryset in serializers

class TrailSectionManager(models.Manager):
    def get_queryset(self):
        queryset = super(TrailSectionManager, self).get_queryset()
        return queryset


class TrailManager(models.Manager):
    def get_queryset(self):
        queryset = super(TrailManager, self).get_queryset()
        queryset = queryset.select_related("location__address")
        return queryset


class EventTrailSectionManager(models.Manager):
    def get_queryset(self):
        queryset = super(EventTrailSectionManager, self).get_queryset()
        return queryset
