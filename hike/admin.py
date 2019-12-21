from django.contrib.gis import admin as gis_admin
from django.contrib.gis import admin

from hikster.helpers.admin import HiksterGeoAdmin, SecureOSM
from .models import (
    Activity,
    Event,
    EventTrailSection,
    Trail,
    TrailActivity,
    TrailImage,
    TrailSection,
    TrailSectionActivity,
)


class TrailImageInlineAdmin(admin.StackedInline):
    model = TrailImage
    extra = 0


class TrailActivityInlineAdmin(admin.TabularInline):
    model = TrailActivity
    extra = 0
    readonly_fields = ["duration", "difficulty"]


class TrailAdminWithSearch(SecureOSM):
    list_per_page = 300
    search_fields = ["name", "trail_id", "location__location_id"]
    actions = ["index_trails"]
    inlines = [TrailActivityInlineAdmin, TrailImageInlineAdmin]
    raw_id_fields = ["location", "region"]


class TrailSectionActivityInlineAdmin(admin.TabularInline):
    model = TrailSectionActivity
    raw_id_fields = ["trail_section"]
    extra = 0


class TrailSectionAdminWithSearch(gis_admin.OSMGeoAdmin):
    search_fields = ["name"]
    inlines = [TrailSectionActivityInlineAdmin]


admin.site.register(Trail, TrailAdminWithSearch)
admin.site.register(TrailSection, TrailSectionAdminWithSearch)
admin.site.register((Activity, Event, EventTrailSection), HiksterGeoAdmin)
