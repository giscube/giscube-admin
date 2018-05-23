import datetime
import json
import os
from haystack import indexes
from django.conf import settings
from django.utils.translation import ugettext as _
from .models import GeoJsonLayer


class GeoJSONLayerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    category_id = indexes.IntegerField(model_attr='category_id', null=True)
    category = indexes.CharField(model_attr='category', null=True)
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description', null=True)
    keywords = indexes.CharField(model_attr='keywords', null=True)
    has_children = indexes.BooleanField()
    children = indexes.CharField()

    def get_model(self):
        return GeoJsonLayer

    def prepare_has_children(self, obj):
        return True

    def prepare_children(self, obj):
        children = []
        url = '%s/layerserver/geojsonlayers/%s/' % (settings.GISCUBE_URL, obj.name)

        children.append({
            'title': _('GeoJSON Layer'),
            'group': False,
            'type': 'GeoJSON',
            'url': url,
            'projection': '4326',
        })

        return json.dumps(children)

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(active=True)