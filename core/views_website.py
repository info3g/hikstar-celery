from django.views.generic import TemplateView

from hikster.hike.models import Activity
from hikster.location.models import Location


class AboutView(TemplateView):
    template_name = "website/core/about.html"


class TOCView(TemplateView):
    template_name = "website/core/toc.html"


class HomeView(TemplateView):
    template_name = "website/core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activities = (
            Activity.objects.filter(id__gt=0).values("id", "name").order_by("id")
        )
        context["activities"] = list(activities)
        context["regions"] = list(
            Location.objects.regions().values("location_id", "name").order_by("name")
        )
        context["location_count"] = Location.objects.count()
        return context
