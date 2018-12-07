# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os

from operator import __or__ as OR

from django.http import (
    HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError,
    FileResponse
)
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication

from .authentication import CsrfExemptSessionAuthentication
from .filters import filterset_factory
from .model_legacy import create_dblayer_model
from .models import GeoJsonLayer, DataBaseLayer
from .pagination import CustomGeoJsonPagination
from .permissions import DBLayerIsValidUser

from .serializers import (
    DBLayerSerializer, DBLayerDetailSerializer,
    create_dblayer_serializer
)
from .utils import geojsonlayer_check_cache


def GeoJSONLayerView(request, layer_name):
    # FIXME: why is this needed?
    # layer_name = ''.join(layer_name.split('.')[:-1])
    layer = GeoJsonLayer.objects.filter(
        active=True,
        name=layer_name).first()
    if layer.visibility == 'private' and not request.user.is_authenticated():
        return HttpResponseForbidden()

    if layer and layer.data_file:
        path = os.path.join(settings.MEDIA_ROOT, layer.data_file.path)
        if os.path.isfile(path):
            geojsonlayer_check_cache(layer)
            return FileResponse(open(path, 'rb'))

    error = {'error': 'DATA_FILE_NOT_FOUND'}
    return HttpResponseServerError(json.dumps(error))


class DBLayerViewSet(viewsets.ModelViewSet):
    lookup_field = 'slug'
    permission_classes = ()
    queryset = []
    model = DataBaseLayer
    serializer_class = DBLayerSerializer
    user_groups = []
    user = None

    def initial(self, request, *args, **kwargs):
        self.user = request.user
        if type(self.user) == AnonymousUser:
            self.user_groups = []
        else:
            self.user_groups = request.user.groups.values_list(
                'name', flat=True)

        return super(DBLayerViewSet,
                     self).initial(
                         request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.filter(active=True)
        if type(self.user) == AnonymousUser:
            qs = qs.filter(
                Q(anonymous_view=True) | Q(
                    anonymous_add=True) | Q(anonymous_delete=True))
        else:
            qs = qs.filter(
                    Q(layer_groups__group__name__in=self.user_groups) | Q(
                        layer_users__user__in=[self.user])).all().distinct()

        return qs


class DBLayerDetailViewSet(DBLayerViewSet):
    serializer_class = DBLayerDetailSerializer


class DBLayerContentViewSet(viewsets.ModelViewSet):
    csrf_exempt = True
    permission_classes = (DBLayerIsValidUser,)
    queryset = []
    model = None
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
    pagination_class = CustomGeoJsonPagination
    page_size_query_param = 'page_size'
    page_size = 50
    ordering_fields = '__all__'
    filter_fields = []
    filter_class = None
    filter_backends = (filters.OrderingFilter,)
    lookup_url_kwarg = 'pk'
    _fields = {}

    def dispatch(self, request, *args, **kwargs):
        self.layer = DataBaseLayer.objects.get(slug=kwargs['layer_slug'])
        self.model = create_dblayer_model(self.layer)
        self.lookup_field = self.layer.pk_field
        self.filter_fields = []
        self._fields = {}
        for field in self.layer.fields.filter(enabled=True):
            if field.search is True:
                self.filter_fields.append(field.field)
            self._fields[field.field] = {
                'fullsearch': field.fullsearch
            }
        lookup_field_value = kwargs.get(self.lookup_url_kwarg)
        defaults = {}
        defaults[self.lookup_field] = lookup_field_value
        kwargs.update(defaults)
        return super(DBLayerContentViewSet,
                     self).dispatch(
                         request, *args, **kwargs)

    def bbox2wkt(self, bbox, srid):
        from django.contrib.gis.geos import GEOSGeometry
        from django.contrib.gis.gdal import SpatialReference, CoordTransform
        bbox = bbox.split(',')
        minx, miny, maxx, maxy = tuple(bbox)
        wkt = ('SRID=4326;'
               'POLYGON ('
               '(%s %s, %s %s, %s %s, %s %s, %s %s))' %
               (minx, miny, maxx, miny, maxx, maxy, minx, maxy, minx, miny))
        geom = GEOSGeometry(wkt, srid=4326)
        if srid != 4326:
            srs_to = SpatialReference(srid)
            srs_4326 = SpatialReference(4326)
            trans = CoordTransform(srs_4326, srs_to)
            geom.transform(trans)
        return geom

    def _geom_filters(self, qs):
        if self.layer.geom_field and 'in_bbox' in self.request.GET:
            in_bbox = self.request.query_params.get('in_bbox', None)
            if in_bbox:
                poly__bboverlaps = '%s__bboverlaps' % self.layer.geom_field
                qs = qs.filter(**{poly__bboverlaps: self.bbox2wkt(
                    in_bbox, self.layer.srid)})
        return qs

    def _fulsearch_filters(self, qs):
        q = self.request.query_params.get('q', None)
        if q:
            lst = []
            for name, field in self._fields.iteritems():
                if field['fullsearch'] is True:
                    if name != self.layer.geom_field:
                        contains = '%s__contains' % name
                        lst.append(Q(**{contains: q}))
            if len(lst) > 0:
                qs = qs.filter(reduce(OR, lst)) # NOQA: E0602
        return qs

    def get_queryset(self):
        qs = self.model.objects.all()
        qs = self._fulsearch_filters(qs)
        qs = self._geom_filters(qs)
        model_filter = filterset_factory(self.model, self.filter_fields)
        qs = model_filter(data=self.request.query_params, queryset=qs)
        qs = qs.filter()
        return qs

    def get_serializer_class(self, *args, **kwargs):
        return create_dblayer_serializer(
            self.model, self._fields.keys(), self.lookup_field)

    def delete_multiple(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    class Meta:
        filter_overrides = ['geom']
