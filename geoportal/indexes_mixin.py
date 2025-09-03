from django.contrib.gis.geos import Polygon

from giscube.models import Category
from giscube.utils import get_giscube_id, prepare_output_data
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
        data = prepare_output_data(obj, data)
        data['title'] = self.prepare_title(obj)
        data['children'] = self.prepare_children(obj)
        data['catalog'] = (obj.category.title or '').split(Category.SEPARATOR) if obj.category else []
        data['catalog_icon'] = self.get_catalog_icon(obj, data['children'])
        data['catalog_color'] = obj.catalog_color if hasattr(obj, 'catalog_color') else None
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

    def get_catalog_icon(self, obj, children):
        if (hasattr(obj, 'shapetype')):
            if (obj.shapetype == 'marker' or obj.shapetype == 'image'):
                return 'place'
            if (obj.shapetype == 'line'):
                return 'timeline'
            if (obj.shapetype == 'polygon'):
                return 'fas fa-draw-polygon'
            if (obj.shapetype == 'circle'):
                return 'fas fa-solid fa-circle'
            return ''
        if (children and len(children) > 0):
            type = children[0]['type'] if children[0] and 'type' in children[0] else None
            if (type and type == 'TMS'):
                return 'las la-table'
            if (type and type == 'WMS'):
                return 'las la-globe'
            return type
        return None
