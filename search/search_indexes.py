from haystack import indexes
from .models import Index


class ObjectIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(model_attr='name', document=True)
    id = indexes.IntegerField(model_attr='id')
    type = indexes.CharField(model_attr='type')
    object_ct_id = indexes.FacetIntegerField(model_attr='obj_ct_id')
    obj_id = indexes.IntegerField(model_attr='obj_id')

    def get_model(self):
        return Index
