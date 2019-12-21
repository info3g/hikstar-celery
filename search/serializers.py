from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import Index
from . import types


class IndexSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        fields = ['name', 'address', 'type', 'url']
        model = Index

    def get_url(self, instance):
        if instance.type == types.TYPE_TRAIL:
            return reverse(
                'trail-detail',
                kwargs={'pk': instance.obj_id},
                request=self.context['request']
            )
        elif instance.type in [types.TYPE_NETWORK, types.TYPE_LOCATION,
                               types.TYPE_MUNICIPALITY, types.TYPE_MOUNTAIN,
                               types.TYPE_REGION]:
            return reverse(
                'trail-list',
                request=self.context['request']
            ) + '?loc={}'.format(instance.obj_id)
        return None
