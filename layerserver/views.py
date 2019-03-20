# -*- coding: utf-8 -*-


import json
import logging
import mimetypes
import os

from operator import __or__ as OR

from django.http import (
    HttpResponseForbidden, HttpResponseServerError, FileResponse
)
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import UploadedFile
from django.forms.models import model_to_dict
from django.utils.functional import cached_property

from rest_framework import filters, parsers, status, views, viewsets
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication

from giscube.models import UserAsset

from .authentication import CsrfExemptSessionAuthentication
from .filters import filterset_factory
from .model_legacy import create_dblayer_model
from .models import GeoJsonLayer, DataBaseLayer
from .pagination import create_geojson_pagination_class
from .permissions import DBLayerIsValidUser, BulkDBLayerIsValidUser

from .serializers import (
    DBLayerSerializer, DBLayerDetailSerializer,
    create_dblayer_serializer
)
from .utils import geojsonlayer_check_cache
from functools import reduce


logger = logging.getLogger(__name__)


def GeoJSONLayerView(request, layer_name):
    # FIXME: why is this needed?
    # layer_name = ''.join(layer_name.split('.')[:-1])
    layer = GeoJsonLayer.objects.filter(
        active=True,
        name=layer_name).first()
    if layer and (layer.visibility == 'private' and not request.user.is_authenticated):
        return HttpResponseForbidden()

    if layer and layer.data_file:
        path = layer.get_data_file_path()
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
    parser_classes = (parsers.MultiPartParser, parsers.JSONParser)
    permission_classes = (DBLayerIsValidUser,)
    queryset = []
    model = None
    authentication_classes = (
        CsrfExemptSessionAuthentication, BasicAuthentication)
    pagination_class = None
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
        self.pagination_class = self.get_pagination_class(self.layer)
        self.filter_fields = []
        self._fields = {}
        only_fields = self.request.GET.get('fields', None)
        if only_fields is not None:
            only_fields = only_fields.split(',') + [self.layer.pk_field, self.layer.geom_field]
        for field in self.layer.fields.filter(enabled=True):
            if only_fields is not None and field.name not in only_fields:
                continue
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
            for name, field in self._fields.items():
                if field['fullsearch'] is True:
                    if name != self.layer.geom_field:
                        contains = '%s__icontains' % name
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

    def get_pagination_class(self, layer):
        page_size = settings.LAYERSERVER_PAGE_SIZE
        if layer.page_size is not None:
            page_size = layer.page_size
        max_page_size = settings.LAYERSERVER_MAX_PAGE_SIZE
        if layer.max_page_size is not None:
            max_page_size = layer.max_page_size
        return create_geojson_pagination_class(page_size=page_size, max_page_size=max_page_size)

    def get_serializer_class(self, *args, **kwargs):
        return create_dblayer_serializer(
            self.model, list(self._fields.keys()), self.lookup_field)

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

    def __init__(self, *args, **kwargs):
        self._fields = {}
        self.opened_files = []
        self.created_objects = []
        self.original_updated_objects = {}
        self.updated_objects = []
        self.user_assets = []

    def dispatch(self, request, *args, **kwargs):
        self.layer = DataBaseLayer.objects.get(slug=kwargs['layer_slug'])
        self.model = create_dblayer_model(self.layer)
        self.lookup_field = self.layer.pk_field
        self.geom_field = self.layer.geom_field
        self._fields = {}
        for field in self.layer.fields.filter(enabled=True):
            self._fields[field.name] = {}
        return super(DBLayerContentBulkViewSet,
                     self).dispatch(
                         request, *args, **kwargs)

    def get_queryset(self):
        qs = self.model.objects.all()
        return qs

    def to_image(self, field, path):
        if path:
            media_path = path.replace('media://', '')
            self.user_assets.append(media_path)
            path = os.path.join(settings.MEDIA_ROOT, media_path)
            image_file = open(path, 'rb')
            self.opened_files.append(image_file)
            file_name = path.split('/')[-1]
            file_mime = mimetypes.guess_type(file_name)
            size = os.path.getsize(path)
            return UploadedFile(image_file, file_name, file_mime, size)

    @cached_property
    def _image_fields(self):
        from .models import DataBaseLayerField
        image_fields = {}
        for field in self.layer.fields.filter(widget=DataBaseLayerField.WIDGET_CHOICES.image):
            image_fields[field.name] = field
        return image_fields

    def apply_widgets(self, items):
        image_fields = self._image_fields
        for item in items:
            for field in image_fields:
                if field in item:
                    item[field] = self.to_image(field, item[field])

    def undo(self):
        self.undo_add()
        self.undo_update()

    def undo_add(self):
        image_fields = self._image_fields
        for item in self.created_objects:
            for field in image_fields:
                file = getattr(item, field, None)
                if file:
                    try:
                        file.delete(save=False)
                    except Exception as e:
                        logger.error(str(e), exc_info=True)

    def undo_update(self):
        """
        - Remove new images
        """
        image_fields = self._image_fields
        for item in self.updated_objects:
            pk = getattr(item, self.lookup_field)
            old_model = self.model(**self.original_updated_objects[pk])
            for field in image_fields:
                old_file = getattr(old_model, field)
                if old_file:
                    file = getattr(item, field, None)
                    if file.path != old_file.path:
                        file.delete(save=False)

    def add(self, items):
        self.apply_widgets(items)
        Serializer = create_dblayer_serializer(
            self.model, list(self._fields.keys()), self.lookup_field)
        add_serializers = []
        for item in items:
            serializer = Serializer(data=item)
            if serializer.is_valid():
                add_serializers.append(serializer)
            else:
                return serializer.errors

        for serializer in add_serializers:
            try:
                self.created_objects.append(serializer.save())
            except Exception:
                self.created_objects.append(serializer.instance)
                raise

    def get_lookup_field_value(self, data):
        if 'properties' in data and isinstance(data['properties'], dict):
            if self.lookup_field not in data['properties'] and 'id' in data:
                return data['id']
        return data[self.lookup_field]

    def update(self, items):
        self.apply_widgets(items)
        Serializer = create_dblayer_serializer(
            self.model, list(self._fields.keys()), self.lookup_field)
        update_serializers = []
        for item in items:
            filter = {}
            filter[self.lookup_field] = self.get_lookup_field_value(item)
            obj = self.model.objects.get(**filter)
            self.original_updated_objects[list(filter.values())[0]] = model_to_dict(obj, exclude=['pk'])
            serializer = Serializer(instance=obj, data=item, partial=True)
            if serializer.is_valid():
                update_serializers.append(serializer)
            else:
                return serializer.errors

        for serializer in update_serializers:
            try:
                self.updated_objects.append(serializer.save())
            except Exception:
                self.updated_objects.append(serializer.instance)
                raise

    def delete(self, items):
        filter = {}
        filter['%s__in' % self.lookup_field] = items
        qs = self.get_queryset().filter(**filter)
        image_fields = self._image_fields
        for item in qs:
            for field in image_fields:
                file = getattr(item, field, None)
                if file is not None:
                    transaction.on_commit(
                        lambda: file.delete(save=False)
                    )
            item.delete()

    def delete_user_assets(self):
        if len(self.user_assets) > 0:
            user_assets = UserAsset.objects.filter(file__in=self.user_assets)
            for asset in user_assets:
                asset.delete()

    def post(self, request, layer_slug):
        data = request.data
        errors = {}

        # TODO: schema
        conn = self.layer.db_connection.connection_name()
        autocommit = transaction.get_autocommit(using=conn)
        transaction.set_autocommit(False, using=conn)

        try:
            if 'ADD' in data and len(data['ADD']) > 0:
                add_errors = self.add(data['ADD'])
                if add_errors:
                    errors['ADD'] = add_errors
                    self.undo()

            if 'UPDATE' in data and len(data['UPDATE']) > 0:
                update_errors = self.update(data['UPDATE'])
                if update_errors:
                    errors['UPDATE'] = update_errors
                    self.undo()

            if 'DELETE' in data and len(data['DELETE']) > 0:
                self.delete(data['DELETE'])

            if len(list(errors.keys())) > 0:
                transaction.rollback(using=conn)
                transaction.set_autocommit(autocommit, using=conn)
                self.undo()
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                transaction.commit(using=conn)
                transaction.set_autocommit(autocommit, using=conn)
                self.delete_user_assets()
                return Response({}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            self.undo()
            transaction.rollback(using=conn)
            transaction.set_autocommit(autocommit, using=conn)
            logger.error('ERROR in DBLayerContentBulkViewSet', exc_info=True)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            for file in self.opened_files:
                try:
                    file.close()
                except Exception as e:
                    if settings.DEBUG:
                        logger.warning(e)
