from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import Location, PointOfInterest


@receiver(post_save, sender=Location)
def set_location_objectid(sender, instance: Location, created, **kwargs):
    if created:
        instance.objectid = instance.location_id
        instance.save()


@receiver(post_save, sender=PointOfInterest)
def set_poi_objectid(sender, instance: PointOfInterest, created, **kwargs):
    if created:
        instance.objectid = instance.poi_id
        instance.save()
