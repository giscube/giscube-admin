from geoportal.indexes_mixin import GeoportalSearchIndexMixin
from giscube.giscube_search_indexes_mixins import ResourcesIndexMixin
from giscube.indexes_mixin import PermissionIndexMixin
from giscube.utils import prepare_children

from .models import Service


class ServiceSearch(ResourcesIndexMixin, PermissionIndexMixin, GeoportalSearchIndexMixin):

    def prepare_children(self, obj):
        children = prepare_children(obj)
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
