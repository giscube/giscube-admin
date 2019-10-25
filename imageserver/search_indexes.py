import json

from django.conf import settings

from haystack import indexes

from giscube.utils import get_giscube_id

from .models import Service


class ServiceIndex(indexes.SearchIndex, indexes.Indexable):
    giscube_id = indexes.CharField(model_attr='pk')
    text = indexes.CharField(document=True, use_template=True)
    category_id = indexes.IntegerField(model_attr='category_id', null=True)
    category = indexes.CharField(model_attr='category', null=True)
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(model_attr='title', null=True, default='')
    description = indexes.CharField(model_attr='description', null=True)
    keywords = indexes.CharField(model_attr='keywords', null=True)
    has_children = indexes.BooleanField()
    children = indexes.CharField()
    options = indexes.CharField()
    private = indexes.BooleanField()

    def get_model(self):
        return Service

    def prepare_has_children(self, obj):
        return True

    def prepare_children(self, obj):
        children = []
        url = '%s/imageserver/services/%s/' % (settings.GISCUBE_URL, obj.name)

        for sl in obj.servicelayer_set.all():
            layer = sl.layer
            children.append({
                'title': layer.title or layer.name,
                'group': False,
                'type': 'WMS',
                'url': url,
                'layers': layer.name,
                'projection': layer.projection,
            })
        return json.dumps(children)

    def prepare_giscube_id(self, obj):
        return get_giscube_id(obj)

    def prepare_options(self, obj):
        return obj.options or '{}'

    def prepare_private(self, obj):
        return obj.visibility == 'private'

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(active=True, visible_on_geoportal=True)
