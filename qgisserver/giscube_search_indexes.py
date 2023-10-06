from django.conf import settings
from django.urls import reverse

from geoportal.indexes_mixin import GeoportalSearchIndexMixin
from giscube.giscube_search_indexes_mixins import ResourcesIndexMixin
from giscube.indexes_mixin import PermissionIndexMixin
from giscube.utils import url_slash_join

from .models import Service


class ServiceSearch(ResourcesIndexMixin, PermissionIndexMixin, GeoportalSearchIndexMixin):

    def prepare_children(self, obj):
        children = []
        service = {
            'title': obj.title or obj.name,
            'description': obj.description,
            'group': False,
            'choose_individual_layers': obj.choose_individual_layers,
            'layers': obj.layers
        }
        if obj.tilecache_enabled:
            url = '%s{z}/{x}/{y}.png' % reverse('qgisserver-tilecache', args=(obj.name,))
            url = url_slash_join(settings.GISCUBE_URL, url)
            service.update({
                'type': 'TMS',
                'url': url,
            })
        else:
            url = url_slash_join(settings.GISCUBE_URL, '/qgisserver/services/%s' % obj.name)
            service.update({
                'type': 'WMS',
                'url': url,
                'layers': obj.default_layer or '',
                'projection': '3857',
                'giscube': {
                    'single_image': obj.wms_single_image,
                    'getfeatureinfo_support': obj.wms_getfeatureinfo_enabled,
                },
            })
        children.append(service)
        return children + super().prepare_children(obj)

    def prepare_output_data(self, obj):
        output_data = super().prepare_output_data(obj)
        output_data['options']['single_image'] = getattr(obj, 'wms_single_image', False)
        output_data['options']['getfeatureinfo_support'] = getattr(obj, 'wms_getfeatureinfo_enabled', False)
        if obj.popup:
            output_data["options"]["popup"] = obj.popup
        return output_data


index_config = [
    ServiceSearch({
        'index': 'geoportal',
        'model': Service
    }),
]
