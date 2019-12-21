from django.db.models import Value, BooleanField
from django.utils.translation import ugettext_lazy as _

from hikster.location.models import PointOfInterestType


def get_poi_types(category_ids=None, with_all=False):
    types = PointOfInterestType.objects.annotate(
        show=Value(True, output_field=BooleanField())
    )

    if category_ids:
        types = types.filter(category__in=category_ids)

    types = types.values("id", "name", "show").distinct().order_by("name")

    if with_all:
        return [{"id": -1, "name": _("All types")}] + list(types)
    return list(types)


def get_poi_categories(with_all=False):
    poi_categories = [
        {
            "id": 1,
            "name": "Hébergement",
            "types": get_poi_types([1], with_all=with_all),
            "show_all": True,
        },
        {
            "id": 3,
            "name": "Stationnement",
            "types": get_poi_types([3], with_all=with_all),
            "show_all": True,
        },
        {
            "id": 4,
            "name": "Activité",
            "types": get_poi_types([4], with_all=with_all),
            "show_all": True,
        },
        {
            "id": 5,
            "name": "Restaurant",
            "types": get_poi_types([5], with_all=with_all),
            "show_all": True,
        },
        {
            "id": 6,
            "name": "Autre",
            "types": get_poi_types([6], with_all=with_all),
            "show_all": True,
        },
    ]

    if with_all:
        return [
            {
                "id": -1,
                "name": _("All categories"),
                "types": get_poi_types([1, 3, 4, 5, 6], with_all=True),
                "show_all": True,
            }
        ] + poi_categories
    return poi_categories
