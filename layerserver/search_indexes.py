import json
from haystack import indexes
from django.conf import settings
from django.utils.translation import ugettext as _
from layerserver.models import GeoJsonLayer, DataBaseLayer


class GeoJSONLayerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    category_id = indexes.IntegerField(model_attr='category_id', null=True)
    category = indexes.CharField(model_attr='category', null=True)
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(model_attr='title', null=True, default='')
    description = indexes.CharField(model_attr='description', null=True)
    keywords = indexes.CharField(model_attr='keywords', null=True)
    has_children = indexes.BooleanField()
    children = indexes.CharField()
    private = indexes.BooleanField()

    def get_model(self):
        return GeoJsonLayer

    def prepare_has_children(self, obj):
        return True

    def prepare_children(self, obj):
        children = []
        url = '%s/layerserver/geojsonlayers/%s/' % (
            settings.GISCUBE_URL, obj.name)

        children.append({
            'title': _('GeoJSON Layer'),
            'group': False,
            'type': 'GeoJSON',
            'url': url,
            'projection': '4326',
        })

        return json.dumps(children)

    def prepare_private(self, obj):
        return obj.visibility == 'private'

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(active=True, visible_on_geoportal=True)


class DataBaseLayerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    category_id = indexes.IntegerField(model_attr='category_id', null=True)
    category = indexes.CharField(model_attr='category', null=True)
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(model_attr='title', null=True, default='')
    description = indexes.CharField(model_attr='description', null=True)
    keywords = indexes.CharField(model_attr='keywords', null=True)
    has_children = indexes.BooleanField()
    children = indexes.CharField()
    private = indexes.BooleanField()

    def get_model(self):
        return DataBaseLayer

    def prepare_has_children(self, obj):
        return True

    def prepare_children(self, obj):
        children = []
        url = '%s/layerserver/databaselayers/%s/' % (
            settings.GISCUBE_URL, obj.name)
        references = []
        for reference in obj.references.all():
            service = reference.service
            service_url = '%s/qgisserver/services/%s/' % (
                settings.GISCUBE_URL, service.name)
            references.append({
                'title': service.title or service.name,
                'url': service_url,
                'projection': '3857'
            })

        children.append({
            'title': _('DataBase Layer'),
            'group': False,
            'type': 'DataBaseLayer',
            'url': url,
            'projection': '4326',
            'references': references
        })

        return json.dumps(children)

    def prepare_private(self, obj):
        return obj.anonymous_view

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(active=True, visible_on_geoportal=True)
