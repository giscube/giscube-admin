from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext as _

from geoportal.indexes_mixin import GeoportalSearchIndexMixin
from giscube.indexes_mixin import PermissionIndexMixin
from giscube.utils import remove_app_url, url_slash_join
from layerserver.models import DataBaseLayer, GeoJsonLayer


class DataBaseLayerIndex(PermissionIndexMixin, GeoportalSearchIndexMixin):
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
        return children


class GeoJsonLayerIndex(PermissionIndexMixin, GeoportalSearchIndexMixin):
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
        return children


index_config = [
    DataBaseLayerIndex({
        'index': 'geoportal',
        'model': DataBaseLayer
    }),
    GeoJsonLayerIndex({
        'index': 'geoportal',
        'model': GeoJsonLayer
    })
]
