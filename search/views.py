from haystack.query import SearchQuerySet
from rest_framework.generics import ListAPIView
from django.db.models import Q
from ..location.models import Location
from ..hike.models import Trail
from .models import Index
from .serializers import IndexSerializer


class SearchView(ListAPIView):
    serializer_class = IndexSerializer

    def get_queryset(self):
        search_term = self.request.GET.get('search_term', None)
        location_ids = self.request.GET.get('locations', None)

        if location_ids:
            location_ids = list(map(int, location_ids.split(',')))

        if not search_term:
            return Index.objects.none()

        sqs = SearchQuerySet().auto_query(search_term)
        id_list = [result.id for result in sqs]

        q_set = Index.objects.filter(id__in=id_list)
        if location_ids is not None:
            trail_ids  = list(Trail.objects.filter(location_id__in=location_ids).values_list('trail_id', flat=True))
            q_set = q_set.filter(Q(type='network', obj_id__in=location_ids) | Q(type='trail', obj_id__in=trail_ids))

        return q_set