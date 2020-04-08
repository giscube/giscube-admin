from django.conf import settings

from geoportal.indexes_mixin import GeoportalSearchIndexMixin
from giscube.indexes_mixin import VisibilityIndexMixin
from giscube.utils import url_slash_join

from .models import Service


class ServiceIndex(VisibilityIndexMixin, GeoportalSearchIndexMixin):
    def prepare_children(self, obj):
        children = []
        url = url_slash_join(settings.GISCUBE_URL, 'imageserver/services/', obj.name)

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
        return children


index_config = [
    ServiceIndex({
        'index': 'geoportal',
        'model': Service
    })
]
