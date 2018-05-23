# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.http import (
    HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError,
    FileResponse
)

from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import GeoJsonLayer, DataBaseLayer
from .model_legacy import create_model
from .serializers import create_serializer


from .serializers import (
    DBLayerSerializer, DBLayerDetailSerializer
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


# class CsrfExemptSessionAuthentication(SessionAuthentication):
#     def enforce_csrf(self, request):
#         return  # To not perform the csrf check previously happening


class DBLayerViewSet(viewsets.ModelViewSet):
    lookup_field = 'slug'
    permission_classes = ()
    queryset = []
    model = DataBaseLayer
    serializer_class = DBLayerSerializer
    user_groups = []
    user = None

    def get_queryset(self, *args, **kwargs):
        return self.model.objects.all()


class DBLayerDetailViewSet(DBLayerViewSet):
    serializer_class = DBLayerDetailSerializer


class DBLayerContentViewSet(viewsets.ModelViewSet):
    csrf_exempt = True
    queryset = []
    model = None
    ordering_fields = '__all__'
    filter_fields = []
    filter_class = None
    lookup_url_kwarg = 'pk'
    _fields = []

    def dispatch(self, request, *args, **kwargs):
        self.layer = DataBaseLayer.objects.get(slug=kwargs['layer_slug'])
        self.model = create_model(
            self.layer.table, {
                'name': self.layer.db_connection.connection_name(),
                'connection': self.layer.db_connection.get_connection()})
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

    def get_queryset(self):
        qs = self.model.objects.all()
        return qs

    def get_serializer_class(self, *args, **kwargs):
        print(self.model, self._fields, self.lookup_field)
        return create_serializer(self.model, self._fields, self.lookup_field)

    def delete_multiple(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
