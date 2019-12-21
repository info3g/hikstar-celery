# Generated by Django 2.1.5 on 2019-04-23 02:52

from django.db import migrations


CAT_ACTIVITY = 4
CAT_RESTAURANT = 5
CAT_PARKING = 3
CAT_ACCOMODATION = 1
CAT_OTHER = 6


categories = {
    CAT_ACTIVITY: [80],
    CAT_RESTAURANT: [44],
    CAT_PARKING: [33],
    CAT_ACCOMODATION: [71, 64, 58, 57, 49, 42, 28, 16, 14, 11, 7],
    CAT_OTHER: [
        79,
        78,
        77,
        75,
        74,
        70,
        69,
        68,
        67,
        51,
        50,
        48,
        47,
        46,
        41,
        40,
        39,
        37,
        32,
        31,
        30,
        29,
        27,
        25,
        23,
        22,
        21,
        20,
        19,
        18,
        9,
        8,
        4,
        3,
        2,
        0,
    ],
}


def populate_poitype_category(apps, schema_editor):
    PointOfInterestType = apps.get_model("location", "PointOfInterestType")

    for key, value in categories.items():
        PointOfInterestType.objects.filter(pk__in=value).update(category=key)


class Migration(migrations.Migration):

    dependencies = [("location", "0036_pointofinteresttype_category")]

    operations = [
        migrations.RunPython(populate_poitype_category, migrations.RunPython.noop)
    ]