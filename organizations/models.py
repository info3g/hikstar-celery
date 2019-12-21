from django.conf import settings
from django.db import models

from hikster.hike.models import Trail, TrailSection
from django.utils import timezone
from django.utils.functional import cached_property
from hikster.utils.models import Address
from hikster.location.models import PointOfInterest


class OrganizationWidget(models.Model):
    organization = models.OneToOneField(
        "Organization", on_delete=models.CASCADE, related_name="widget"
    )
    max_widget_loads = models.IntegerField(default=0)
    max_page_loads = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.organization.name


class Organization(models.Model):
    name = models.CharField(max_length=128)
    contact = models.CharField(max_length=128, null=True, blank=True)
    address = models.OneToOneField(
        Address, null=True, blank=True, on_delete=models.CASCADE
    )
    aid = models.CharField(max_length=500, default=None, null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not hasattr(self, "widget"):
            OrganizationWidget.objects.create(organization=self)

    def get_location_shape_query(self):
        location_buffered_shapes = [
            location.shape.buffer(0.02)
            for location in self.locations.all()
            if location.shape is not None
        ]

        # Turn the list of location shapes into a list of Q objects
        queries = [models.Q(shape__within=shape) for shape in location_buffered_shapes]

        if not queries:
            return None

        # Take one Q object from the list
        query = queries.pop()
        # Or the Q object with the ones remaining in the list
        for item in queries:
            query |= item

        return query

    @property
    def trail_sections(self):
        query = self.get_location_shape_query()

        if query is None:
            return TrailSection.objects.none()

        return TrailSection.objects.filter(query)

    @property
    def point_of_interests(self):
        query = self.get_location_shape_query()

        if query is None:
            return PointOfInterest.objects.none()

        return PointOfInterest.objects.filter(query)

    @property
    def trails(self):
        return Trail.objects.filter(location__in=self.locations.all())

    @cached_property
    def total_widget_loads(self):
        return self.widget_loads.count()

    @cached_property
    def current_month_widget_loads(self):
        current_date = timezone.now().date()
        return self.widget_loads.filter(
            date_created__year=current_date.year, date_created__month=current_date.month
        ).count()

    @cached_property
    def total_page_loads(self):
        return self.page_loads.count()

    @cached_property
    def current_month_page_loads(self):
        current_date = timezone.now().date()
        return self.page_loads.filter(
            date_created__year=current_date.year, date_created__month=current_date.month
        ).count()

    @property
    def consumed_max_widget_loads(self):
        return self.current_month_widget_loads >= self.widget.max_widget_loads

    @property
    def consumed_max_page_loads(self):
        return self.current_month_page_loads >= self.widget.max_page_loads


class WidgetLoad(models.Model):
    organization = models.ForeignKey(
        "Organization", on_delete=models.CASCADE, related_name="widget_loads"
    )
    referrer = models.CharField(max_length=255, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.organization.name


class PageLoad(models.Model):
    organization = models.ForeignKey(
        "Organization", on_delete=models.CASCADE, related_name="page_loads"
    )
    widget_load = models.ForeignKey(
        "WidgetLoad", on_delete=models.CASCADE, related_name="page_loads"
    )
    referrer = models.CharField(max_length=255, blank=True)
    url = models.URLField(max_length=255, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.organization.name


class OrganizationMember(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="members"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("organization", "user")

    def __str__(self):
        return "{} -> {}".format(self.organization, self.user)
