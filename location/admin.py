from django.contrib.gis import admin

from django.contrib.gis.db import models
from django.forms.widgets import Textarea
from hikster.helpers.admin import SecureOSM
from .models import (
    Location,
    LocationImage,
    PointOfInterest,
    PointOfInterestImage,
    PointOfInterestType,
)


class LocationImageInlineAdmin(admin.StackedInline):
    model = LocationImage
    extra = 0


class PointOfInterestImageInlineAdmin(admin.StackedInline):
    model = PointOfInterestImage
    extra = 0


class LocationWithSearch(admin.ModelAdmin):
    list_display = ["location_id", "name", "type"]
    list_per_page = 300
    search_fields = ["location_id", "name", "network", "type"]
    actions = ["index_locations"]
    inlines = [LocationImageInlineAdmin]
    list_filter = ["type"]
    raw_id_fields = ["organization", "address"]
    formfield_overrides = {models.GeometryField: {"widget": Textarea}}


class PoiWithSearch(admin.ModelAdmin):
    search_fields = ["poi_id", "name"]
    inlines = [PointOfInterestImageInlineAdmin]
    formfield_overrides = {models.GeometryField: {"widget": Textarea}}


admin.site.register(Location, LocationWithSearch)
admin.site.register(PointOfInterest, PoiWithSearch)
admin.site.register((PointOfInterestType,), SecureOSM)
