from collections import OrderedDict

from rest_framework import pagination
from rest_framework.response import Response


class GeoJsonPagination(pagination.PageNumberPagination):
    """
    A geoJSON implementation of a pagination serializer.
    """
    page_size_query_param = 'page_size'
    page_size = 50
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('type', 'FeatureCollection'),
            ('count', self.page.paginator.count),
            ('from', self.page.start_index()),
            ('to', self.page.end_index()),
            ('page', self.page.number),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.get_page_size(self.request)),
            ('total_pages', self.page.paginator.num_pages),
            ('features', data['features']),
        ]))


def create_geojson_pagination_class(page_size=50, max_page_size=1000):
    attrs = {
        '__module__': 'layerserver',
        'Meta': type(str('Meta'), (object,), {
        })
    }
    attrs['page_size'] = page_size
    attrs['max_page_size'] = max_page_size

    return type(str('CustomGeoJsonPagination'), (GeoJsonPagination,), attrs)
