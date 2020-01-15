import json

from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext as _

from haystack import indexes

from giscube.utils import get_giscube_id, remove_app_url, url_slash_join

from .models import DataBaseLayer, GeoJsonLayer


class GeoJSONLayerIndex(indexes.SearchIndex, indexes.Indexable):
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
    private = indexes.BooleanField()
    legend = indexes.CharField(model_attr='legend', null=True)

    def get_model(self):
        return GeoJsonLayer

    def prepare_has_children(self, obj):
        return True

    def prepare_category(self, obj):
        return obj.category.title if hasattr(obj, 'category') and obj.category else None

    def prepare_children(self, obj):
        children = []
        url = url_slash_join(
            settings.GISCUBE_URL, remove_app_url(reverse('geojsonlayer', kwargs={'name': obj.name})))
        children.append({
            'title': _('GeoJSON Layer'),
            'group': False,
            'type': 'GeoJSON',
            'url': url,
            'projection': '4326',
        })

        return json.dumps(children)

    def prepare_giscube_id(self, obj):
        return get_giscube_id(obj)

    def prepare_private(self, obj):
        return obj.visibility == 'private'

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(active=True, visible_on_geoportal=True)


class DataBaseLayerIndex(indexes.SearchIndex, indexes.Indexable):
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
    private = indexes.BooleanField()
    legend = indexes.CharField(model_attr='legend', null=True)

    def get_model(self):
        return DataBaseLayer

    def prepare_has_children(self, obj):
        return True

    def prepare_category(self, obj):
        return obj.category.title if hasattr(obj, 'category') and obj.category else None

    def prepare_children(self, obj):
        children = []
        url = url_slash_join(settings.GISCUBE_URL, '/layerserver/databaselayers/%s/' % obj.name)
        if obj.geom_field is not None:
            references = []
            for reference in obj.references.all():
                service = reference.service
                service_url = url_slash_join(settings.GISCUBE_URL, '/qgisserver/services/%s/' % service.name)
                references.append({
                    'title': service.title or service.name,
                    'url': service_url,
                    'projection': '3857'
                })
            children.append({
                'title': _('DataBase Layer'),
                'group': False,
                'type': 'DataBaseLayer',
                'format': 'GeoJSON',
                'url': url,
                'projection': '4326',
                'references': references
            })
        else:
            children.append({
                'title': _('DataBase Layer'),
                'group': False,
                'type': 'DataBaseLayer',
                'format': 'JSON',
                'url': url
            })
        return json.dumps(children)

    def prepare_giscube_id(self, obj):
        return get_giscube_id(obj)

    def prepare_private(self, obj):
        return not obj.anonymous_view

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(active=True, visible_on_geoportal=True)
