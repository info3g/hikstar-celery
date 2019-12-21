from django.db.models.signals import post_delete, post_save

from .models import INDEXABLE, Index


def add_to_index(sender, instance, created, **kwargs):
    if not isinstance(instance, INDEXABLE):
        return

    Index.objects.add(instance)


post_save.connect(add_to_index, dispatch_uid='add-to-index')


def remove_from_index(sender, instance, using, **kwargs):
    if not isinstance(instance, INDEXABLE):
        return

    Index.objects.remove(instance)


post_delete.connect(remove_from_index, dispatch_uid='remove-from-index')
