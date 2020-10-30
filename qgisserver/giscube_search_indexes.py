from django.conf import settings

from geoportal.indexes_mixin import GeoportalSearchIndexMixin
from giscube.giscube_search_indexes_mixins import ResourcesIndexMixin
from giscube.indexes_mixin import VisibilityIndexMixin
from giscube.utils import url_slash_join

from .models import Service


class ServiceSearch(ResourcesIndexMixin, VisibilityIndexMixin, GeoportalSearchIndexMixin):

    def prepare_children(self, obj):
        children = []
        url = url_slash_join(settings.GISCUBE_URL, '/qgisserver/services/%s' % obj.name)
        children.append({
            'title': obj.title,
            'group': False,
            'type': 'WMS',
            'url': url,
            'layers': obj.default_layer or '',
            'projection': '3857',
        })
        return children + super().prepare_children(obj)


index_config = [
    ServiceSearch({
        'index': 'geoportal',
        'model': Service
    }),
]
