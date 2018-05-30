# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.http import (
    HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError,
    FileResponse
)
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

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


def GeoJSONLayerView(request, layer_name):
    # FIXME: why is this needed?
    # layer_name = ''.join(layer_name.split('.')[:-1])
    layer = GeoJsonLayer.objects.filter(
        active=True,
        name=layer_name).first()
    if not layer or not layer.data_file:
        return HttpResponseNotFound()
    if layer.visibility == 'private' and not request.user.is_authenticated():
        return HttpResponseForbidden()

    path = layer.data_file.path

    if not os.path.isfile(path):
        return HttpResponseServerError(path)

    return FileResponse(open(path, 'rb'))


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
    _fields = []

    def dispatch(self, request, *args, **kwargs):
        self.layer = DataBaseLayer.objects.get(slug=kwargs['layer_slug'])
        self.model = create_dblayer_model(self.layer)
        self.lookup_field = self.layer.pk_field
        self._fields = list(self.layer.fields.filter(
            enabled=True).values_list('field', flat=True))
        self.filter_fields = self._fields
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

    def get_queryset(self):
        qs = self.model.objects.all()
        if self.layer.geom_field:
            in_bbox = self.request.query_params.get('in_bbox', None)
            if in_bbox:
                poly__bboverlaps = '%s__bboverlaps' % self.layer.geom_field
                qs = qs.filter(**{poly__bboverlaps: self.bbox2wkt(
                    in_bbox, self.layer.srid)})
        model_filter = filterset_factory(self.model, self.filter_fields)
        qs = model_filter(data=self.request.query_params, queryset=qs)
        qs = qs.filter()
        return qs

    def get_serializer_class(self, *args, **kwargs):
        return create_dblayer_serializer(
            self.model, self._fields, self.lookup_field)

    def delete_multiple(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    class Meta:
        filter_overrides = ['geom']
