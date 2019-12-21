from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from hikster.organizations.models import Organization, PageLoad, WidgetLoad


class PageLoadMixin(object):
    def set_page_load(self):
        request = self.request
        session = self.request.session

        if "widget" not in request.path:
            return

        org = get_object_or_404(Organization, pk=session.get("widget_org_id"))

        if org.consumed_max_page_loads:
            return JsonResponse({"error": _("Max page load exceeded")})

        try:
            widget_load = WidgetLoad.objects.get(pk=session.get("widget_load_id"))
        except WidgetLoad.DoesNotExist:
            widget_load = None

        PageLoad.objects.create(
            organization=org,
            widget_load=widget_load,
            referrer=self.request.META.get("HTTP_REFERER", ""),
            url=self.request.get_raw_uri(),
        )
