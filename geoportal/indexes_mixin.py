import ujson as json

from django.contrib.gis.geos import Polygon

from giscube.models import Category
from giscube.utils import get_giscube_id
from giscube_search.base_index import BaseGeomIndexMixin, BaseModelIndex


class GeoportalSearchIndexMixin(BaseGeomIndexMixin, BaseModelIndex):
    def get_items(self):
        qs = super().get_items()
        qs = qs.filter(active=True)
        return qs

    def get_config_fields(self):
        return ['name', 'title', 'keywords', 'metadata.provider_name', 'category.title', 'description']

    def get_config_search_data(self):
        return ['name', 'category.pk', 'metadata.date', 'visible_on_geoportal']

    def get_config_search_data_keys(self):
        return ['name', 'category_id', 'date', 'visible_on_geoportal']

    def prepare_children(self, obj):
        return []

    def prepare_output_data(self, obj):
        data = super().prepare_output_data(obj)
        data['giscube_id'] = get_giscube_id(obj)
        data['private'] = not obj.anonymous_view
        data['category_id'] = obj.category.pk if obj.category else None
        data['title'] = self.prepare_title(obj)
        data['description'] = obj.description
        data['keywords'] = obj.keywords
        data['group'] = True
        data['has_children'] = True
        data['children'] = self.prepare_children(obj)
        data['legend'] = getattr(obj, 'legend', None)
        data['visible_on_geoportal'] = getattr(obj, 'visible_on_geoportal', False)
        data['options'] = json.loads(getattr(obj, 'options', '{}') or '{}')
        data['catalog'] = (obj.category.title or '').split(Category.SEPARATOR) if obj.category else []
        metadata_data = [
            'date', 'language', 'category.name', 'information', 'provider_name', 'provider_web', 'provider_email',
            'summary', 'bbox'
        ]
        metadata_data_keys = [
            'date', 'language', 'category', 'information', 'provider_name', 'provider_web', 'provider_email',
            'summary', 'bbox'
        ]
        metadata = {}
        for k, x in zip(metadata_data_keys, metadata_data):
            metadata[k] = self.get_value(obj, 'metadata.%s' % x)
        data['metadata'] = metadata
        return data

    def prepare_search_data(self, obj):
        data = super().prepare_search_data(obj)
        data['giscube_id'] = get_giscube_id(obj)
        return data

    def prepare_geom_field(self, obj):
        meta = getattr(obj, 'metadata', None)
        if meta and meta.bbox:
            bb = meta.bbox.split(',')
            return Polygon.from_bbox(bb)

    def prepare_title(self, obj):
        return obj.title or obj.name
