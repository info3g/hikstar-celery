from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from hikster.hike.models import Trail
from hikster.location.models import Location
from . import types


INDEXABLE = (Trail, Location)


class IndexManager(models.Manager):
    def add(self, obj):
        """
        Adds an object to the index. If the index already exists for this
        object, it is updated. If it does not exist, it is created.

        :param obj: the object to add to the index

        :return: the index instance

        """
        if not isinstance(obj, INDEXABLE):
            raise Exception('Invalid index object')

        if not obj.name:
            return

        ct = ContentType.objects.get_for_model(obj)
        try:
            idx = self.get(obj_ct=ct, obj_id=getattr(obj, obj.id_field))

        except ObjectDoesNotExist:
            idx = self.model(obj=obj)

        idx.name = obj.name
        idx.type = obj.index_type
        if hasattr(obj, 'location') and obj.location and obj.location.address:
            idx.address = str(obj.location.address)
        elif hasattr(obj, 'address') and obj.address:
            idx.address = str(obj.address)
        idx.save()

        return idx

    def remove(self, obj):
        """
        Removes an object from the index.

        :param obj: the object to remove from the index.

        """
        if not isinstance(obj, INDEXABLE):
            raise Exception('Invalid index object')

        ct = ContentType.objects.get_for_model(obj)
        try:
            idx = self.get(obj_ct=ct, obj_id=getattr(obj, obj.id_field))

        except ObjectDoesNotExist:
            return

        idx.delete()


class Index(models.Model):
    objects = IndexManager()

    TYPE_CHOICES = (
        (types.TYPE_TRAIL, 'Trail'),
        (types.TYPE_MUNICIPALITY, 'Municipality'),
        (types.TYPE_MOUNTAIN, 'Mountain'),
        (types.TYPE_REGION, 'Region'),
        (types.TYPE_NETWORK, 'Network'),
        (types.TYPE_LOCATION, 'Location')
    )

    name = models.CharField(max_length=250, null=False)
    obj_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    obj_id = models.PositiveIntegerField()
    obj = GenericForeignKey(ct_field='obj_ct', fk_field='obj_id')
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    address = models.CharField(max_length=256, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('obj_ct', 'obj_id')
