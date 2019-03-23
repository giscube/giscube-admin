import json
from haystack import indexes
from geoportal.models import Dataset


class DatasetIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    category_id = indexes.IntegerField(model_attr='category_id', null=True)
    category = indexes.CharField(model_attr='category', null=True)
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(model_attr='title', null=True, default='')
    description = indexes.CharField(model_attr='description', null=True)
    keywords = indexes.CharField(model_attr='keywords', null=True)
    has_children = indexes.BooleanField()
    children = indexes.CharField()

    def get_model(self):
        return Dataset

    def prepare_has_children(self, obj):
        return True

    def prepare_children(self, obj):
        children = []
        for r in obj.resources.all():
            children.append({
                'title': r.title or r.name,
                'group': False,
                'type': r.type,
                'url': r.url,
                'layers': r.layers,
                'projection': r.projection,
            })
        return json.dumps(children)

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(active=True)
