# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os

from operator import __or__ as OR

from django.http import (
    HttpResponseForbidden, HttpResponseServerError, FileResponse
)
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

from rest_framework import filters, status, views, viewsets
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication

from .authentication import CsrfExemptSessionAuthentication
from .filters import filterset_factory
from .model_legacy import create_dblayer_model
from .models import GeoJsonLayer, DataBaseLayer
from .pagination import CustomGeoJsonPagination
from .permissions import DBLayerIsValidUser, BulkDBLayerIsValidUser

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
    user = None

    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.filter(active=True)
        filter_anonymous = Q(anonymous_view=True) | Q(anonymous_add=True) | Q(anonymous_update=True) \
            | Q(anonymous_delete=True)

        if type(self.request.user) is AnonymousUser:
            qs = qs.filter(filter_anonymous)
        else:
            self.user_groups = self.request.user.groups.values_list('name', flat=True)
            filter_group = Q(layer_groups__group__name__in=self.user_groups) & Q(
                Q(layer_groups__can_view=True) | Q(layer_groups__can_add=True) | Q(layer_groups__can_update=True) |
                Q(layer_groups__can_delete=True))

            filter_user = Q(layer_users__user=self.request.user) & Q(
                Q(layer_users__can_view=True) | Q(layer_users__can_add=True) |
                Q(layer_users__can_update=True) | Q(layer_users__can_delete=True))
            qs = qs.filter(Q(filter_anonymous) | Q(filter_user) | Q(filter_group))

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
                self.filter_fields.append(field.name)
            self._fields[field.name] = {
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

    def _fullsearch_filters(self, qs):
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
        qs = self._fullsearch_filters(qs)
        qs = self._geom_filters(qs)
        model_filter = filterset_factory(self.model, self.filter_fields)
        qs = model_filter(data=self.request.query_params, queryset=qs)
        qs = qs.filter()
        return qs

    def get_serializer_class(self, *args, **kwargs):
        return create_dblayer_serializer(
            self.model, self._fields.keys(), self.lookup_field)

    # def delete_multiple(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     queryset.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)

    class Meta:
        filter_overrides = ['geom']


class DBLayerContentBulkViewSet(views.APIView):
    csrf_exempt = True
    permission_classes = (BulkDBLayerIsValidUser,)
    queryset = []
    model = None
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
    lookup_url_kwarg = 'pk'
    _fields = {}

    def dispatch(self, request, *args, **kwargs):
        self.layer = DataBaseLayer.objects.get(slug=kwargs['layer_slug'])
        self.model = create_dblayer_model(self.layer)
        self.lookup_field = self.layer.pk_field
        self._fields = {}
        for field in self.layer.fields.filter(enabled=True):
            self._fields[field.name] = {}
        return super(DBLayerContentBulkViewSet,
                     self).dispatch(
                         request, *args, **kwargs)

    def get_queryset(self):
        qs = self.model.objects.all()
        return qs

    def post(self, request, layer_slug):
        data = request.data
        response = {'ADD': [], 'UPDATE': [], 'DELETE': []}
        errors = {}
        autocommit = transaction.get_autocommit()
        transaction.set_autocommit(False)
        try:
            if 'ADD' in data and len(data['ADD']) > 0:
                to_add = data['ADD']
                Serializer = create_dblayer_serializer(
                    self.model, self._fields.keys(), self.lookup_field)
                serializer = Serializer(data=to_add, many=True)
                if serializer.is_valid():
                    response['ADD'] = serializer.to_representation(
                        serializer.save())
                else:
                    errors['ADD'] = serializer.errors

            if 'UPDATE' in data and len(data['UPDATE']) > 0:
                to_update = data['UPDATE']
                ids = []
                for item in to_update:
                    if 'geometry' in item and type(item['geometry']) is dict:
                        ids.append(item['id'])
                    else:
                        ids.append(item[self.lookup_field])
                filter = '%s__in' % self.lookup_field
                qs = self.get_queryset().filter(**{filter: ids})
                if len(ids) != qs.count():
                    raise Exception('ITEM_NOT_FOUND')
                Serializer = create_dblayer_serializer(
                    self.model, self._fields.keys(), self.lookup_field, map_id_field=True)
                serializer = Serializer(instance=qs, data=to_update, many=True, partial=True)
                if serializer.is_valid():
                    response['UPDATE'] = serializer.to_representation(
                        serializer.save())
                else:
                    errors['UPDATE'] = serializer.errors

            if 'DELETE' in data and len(data['DELETE']) > 0:
                to_delete = data['DELETE']
                filter = '%s__in' % self.lookup_field
                qs = self.get_queryset().filter(**{filter: to_delete})
                ids = qs.values_list(self.lookup_field, flat=True)
                for item in qs:
                    item.delete()
                response['DELETE'] = ids

            if errors:
                transaction.rollback()
                transaction.set_autocommit(autocommit)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                transaction.commit()
                transaction.set_autocommit(autocommit)
                return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.rollback()
            transaction.set_autocommit(autocommit)
            if e.message == 'ITEM_NOT_FOUND':
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                raise
