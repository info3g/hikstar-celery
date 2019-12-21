from django.contrib import admin

from . import models


class OrganizationWidgetInlineAdmin(admin.TabularInline):
    model = models.OrganizationWidget


class OrganizationMemberInlineAdmin(admin.TabularInline):
    model = models.OrganizationMember
    extra = 0
    raw_id_fields = ["user"]


@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    inlines = [OrganizationWidgetInlineAdmin, OrganizationMemberInlineAdmin]
    readonly_fields = [
        "current_month_widget_loads",
        "current_month_page_loads",
        "total_widget_loads",
        "total_page_loads",
    ]


@admin.register(models.WidgetLoad)
class WidgetLoadAdmin(admin.ModelAdmin):
    list_display = ("organization", "date_created")


@admin.register(models.PageLoad)
class PageLoadAdmin(admin.ModelAdmin):
    list_display = ("organization", "date_created")
