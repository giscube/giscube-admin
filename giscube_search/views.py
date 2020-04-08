import ujson as json

from django.contrib.gis.gdal.error import SRSException
from django.contrib.gis.geos import GEOSGeometry

from rest_framework.response import Response
from rest_framework.views import APIView

import giscube.settings as custom_settings


class SearchException(Exception):
    pass


class SearchView(APIView):
    def filter_by_content_type(self, request, qs):
        e = request.GET.get('e', None)
        if e:
            content_types = list(filter(None, e.split(',')))
            qs = qs.filter(content_type__in=content_types)
        return qs

    def filter_by_q(self, request, qs):
        q = request.GET.get('q', None)
        if q:
            qs = qs.search(q)
        return qs

    def filter_by_search_data(self, request, qs):
        search_data_field = 'data'
        filters = {}
        for key, value in request.GET.items():
            if key.startswith('search_data_'):
                filters['%s__%s' % (search_data_field, key[14:])] = value
        if len(filters.keys()) > 0:
            qs = qs.filter(**filters)

        return qs

    def limit_query(self, qs):
        if custom_settings.GISCUBE_SEARCH_MAX_RESULTS:
            qs = qs[:int(custom_settings.GISCUBE_SEARCH_MAX_RESULTS)]
        return qs

    def apply_all_filters(self, request, qs):
        qs = self.filter_by_content_type(request, qs)
        qs = self.filter_by_q(request, qs)
        return qs

    def get_queryset(self, request):
        qs = self.get_model().objects.all()
        qs = self.apply_all_filters(request, qs)
        qs = self.limit_query(qs)
        return qs

    def get_data(self, request):
        return [x.output_data for x in self.get_queryset(request)]

    def get(self, request):
        data = self.get_data(request)
        return Response({'results': data})


class GeomSearchView(SearchView):
    def get_epsg(self, request):
        try:
            epsg = int(request.GET.get('epsg', '4326'))
        except Exception:
            raise SearchException('ERROR: invalid epsg value')
        return epsg

    def transform(self, geom, epsg):
        if epsg != 4326:
            try:
                geom.transform(4326)
            except SRSException:
                raise SearchException('ERROR: Geometry transform to 4326')

    def filter_by_distance(self, request, qs):
        epsg = self.get_epsg(request)
        p = request.GET.get('p', None)
        if p:
            try:
                xy = p.split(',')
                xy = list(map(float, xy))
            except Exception:
                raise SearchException('ERROR: invalid p')

            try:
                geom = GEOSGeometry('POINT (%s %s)' % (xy[1], xy[0]), srid=epsg)
            except Exception:
                raise SearchException('ERROR: invalid p value')

            self.transform(geom, epsg)

            try:
                r = request.GET.get('r', 25)
                r = int(r)
            except Exception:
                raise SearchException('ERROR: invalid r value')

            qs = qs.geo_distance(geom, int(r))

        return qs

    def filter_by_geom(self, request, qs):
        epsg = self.get_epsg(request)
        parameters = ('intersects', 'contains',)
        for parameter in parameters:
            wtk = request.GET.get(parameter, None)
            if wtk:
                try:
                    geom = GEOSGeometry(wtk, srid=epsg)
                except Exception:
                    raise SearchException('ERROR: invalid %s value' % parameter)
                qs = getattr(qs, 'geo_%s' % parameter)(geom)
        return qs

    def apply_all_filters(self, request, qs):
        qs = super().apply_all_filters(request, qs)
        qs = self.filter_by_distance(request, qs)
        qs = self.filter_by_geom(request, qs)
        return qs

    def handle_geom_item(self, item, epsg):
        if epsg:
            epsg_value = None
            try:
                geom = GEOSGeometry(json.dumps(item['geom']), 4326)
                geom.transform(epsg)
                epsg_value = json.loads(geom.json)
            except SRSException as e:
                item['epsg_error'] = str(e)
            except Exception:
                item['epsg_error'] = 'ERROR'
            item['geom'] = epsg_value

    def get_data(self, request):
        qs = self.get_queryset(request)
        data = []
        for x in qs:
            item = x.output_data
            self.handle_geom_item(item, request.GET.get('epsg', None))
            data.append(item)
        return data
