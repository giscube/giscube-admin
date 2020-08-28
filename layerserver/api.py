import json
import logging
import mimetypes
import os
import warnings

from functools import reduce
from operator import __or__ as OR

from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import FileResponse, Http404, HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import get_object_or_404
from django.utils.cache import patch_response_headers
from django.utils.functional import cached_property

from rest_framework import filters, parsers, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from giscube.cache_utils import giscube_transaction_cache_response
from giscube.models import UserAsset

from .filters import filterset_factory
from .mapserver import SUPORTED_SHAPE_TYPES, MapserverLayer
from .model_legacy import create_dblayer_model
from .models import DataBaseLayer, GeoJsonLayer
from .pagination import create_geojson_pagination_class, create_json_pagination_class
from .permissions import BulkDBLayerIsValidUser, DBLayerIsValidUser
from .serializers import DBLayerDetailSerializer, DBLayerSerializer, GeoJSONLayerSerializer, create_dblayer_serializer
from .utils import geojsonlayer_check_cache


logger = logging.getLogger(__name__)


class GeoJSONLayerViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'name'
    permission_classes = ()
    queryset = []
    model = GeoJsonLayer
    serializer_class = GeoJSONLayerSerializer

    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.filter(active=True)
        filter_anonymous = Q(anonymous_view=True)

        if self.request.user.is_anonymous:
            qs = qs.filter(filter_anonymous)
        else:
            self.user_groups = self.request.user.groups.values_list('name', flat=True)
            filter_authenticated_user_view = Q(authenticated_user_view=True)
            filter_group = (
                Q(group_permissions__group__name__in=self.user_groups) & Q(group_permissions__can_view=True))
            filter_user = Q(user_permissions__user=self.request.user) & Q(user_permissions__can_view=True)
            qs = qs.filter(
                filter_anonymous | filter_authenticated_user_view | filter_user | filter_group).distinct()

        return qs

    def retrieve(self, request, name):
        layer = self.get_queryset().filter(name=name).first()
        if layer is None:
            raise Http404

        if layer and layer.data_file:
            path = layer.get_data_file_path()
            if os.path.isfile(path):
                geojsonlayer_check_cache(layer)
                return FileResponse(open(path, 'rb'))

        error = {'error': 'DATA_FILE_NOT_FOUND'}
        return HttpResponseServerError(json.dumps(error))


class DBLayerViewSet(viewsets.ModelViewSet):
    lookup_field = 'name'
    permission_classes = ()
    queryset = []
    model = DataBaseLayer
    serializer_class = DBLayerSerializer
    user = None

    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.filter(active=True)
        filter_anonymous = Q(anonymous_view=True) | Q(anonymous_add=True) | Q(anonymous_update=True) \
            | Q(anonymous_delete=True)

        if self.request.user.is_anonymous:
            qs = qs.filter(filter_anonymous)
        else:
            self.user_groups = self.request.user.groups.values_list('name', flat=True)
            filter_group = Q(group_permissions__group__name__in=self.user_groups) & Q(
                Q(group_permissions__can_view=True) | Q(group_permissions__can_add=True) | Q(
                    group_permissions__can_update=True) | Q(group_permissions__can_delete=True))
            filter_user = Q(user_permissions__user=self.request.user) & Q(
                Q(user_permissions__can_view=True) | Q(user_permissions__can_add=True) | Q(
                    user_permissions__can_update=True) | Q(user_permissions__can_delete=True))
            qs = qs.filter(Q(filter_anonymous) | Q(filter_user) | Q(filter_group)).distinct()

        return qs


class DBLayerDetailViewSet(DBLayerViewSet):
    serializer_class = DBLayerDetailSerializer

    def shapetype_not_suported(self, shapetype):
        return HttpResponseServerError('shapetype [%s] not suported' % shapetype)

    @action(methods=['get'], detail=True)
    def wms(self, request, name):
        layer = self.get_object()
        if layer.shapetype not in SUPORTED_SHAPE_TYPES:
            return self.shapetype_not_suported(layer.shapetype)
        ms = MapserverLayer(layer)
        return ms.wms(request)


class PageSize0NotAllowedException(Exception):
    pass


class DBLayerContentViewSetMixin(object):
    def get_model_serializer_class(self):
        fields = list(self._fields.keys())
        return create_dblayer_serializer(
            self.model, fields, self.lookup_field, self.readonly_fields, self._virtual_fields)

    def _virtual_fields_get_queryset(self, qs):
        for field in self._virtual_fields.values():
            qs = field.widget_class.get_queryset(qs, field, self.request)
        return qs

    @cached_property
    def _virtual_fields(self):
        return {field.name: field for field in self.layer.virtual_fields.filter(enabled=True)}


class DBLayerContentViewSet(DBLayerContentViewSetMixin, viewsets.ModelViewSet):
    parser_classes = (parsers.MultiPartParser, parsers.JSONParser)
    permission_classes = (DBLayerIsValidUser,)
    queryset = []
    model = None
    pagination_class = None
    page_size_query_param = 'page_size'
    page_size = 50
    ordering_fields = '__all__'
    filter_fields = []
    filter_class = None
    filter_backends = (filters.OrderingFilter,)
    lookup_url_kwarg = 'pk'
    _fields = {}
    readonly_fields = []

    def dispatch(self, request, *args, **kwargs):
        self.layer = DataBaseLayer.objects.filter(name=kwargs['name']).first()
        if self.layer is None:
            raise Http404
        self.model = create_dblayer_model(self.layer)
        self.lookup_field = self.layer.pk_field
        try:
            self.pagination_class = self.get_pagination_class(self.layer)
        except PageSize0NotAllowedException:
            return HttpResponseBadRequest()
        self.filter_fields = []
        self._fields = {}
        self.readonly_fields = []
        only_fields = self.request.GET.get('fields', None)
        if only_fields is not None:
            only_fields = list(filter(None, only_fields.split(','))) + [self.layer.pk_field, self.layer.geom_field]
        for field in self.layer.fields.filter(enabled=True):
            if only_fields is not None and field.name not in only_fields:
                continue
            if field.search is True:
                self.filter_fields.append(field.name)
            self._fields[field.name] = {
                'fullsearch': field.fullsearch
            }
            if field.readonly is True:
                self.readonly_fields.append(field.name)
        lookup_field_value = kwargs.get(self.lookup_url_kwarg)
        defaults = {}
        defaults[self.lookup_field] = lookup_field_value
        kwargs.update(defaults)
        return super(DBLayerContentViewSet,
                     self).dispatch(
                         request, *args, **kwargs)

    def get_serializer_class(self):
        return self.get_model_serializer_class()

    def bbox2wkt(self, bbox, srid):
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

    def geom_from_intersects_param(self, intersects, srid):
        if intersects.startswith('POLYGON'):
            geom = GEOSGeometry(intersects, srid=4326)
            warnings.warn(
                'WKT POLYGON in intersects parameter is deprecated, use coordinates instead', DeprecationWarning
            )
        else:
            coordinates = list(map(float, intersects.split(',')))
            pairs = list(zip(coordinates[0::2], coordinates[1::2]))
            geom = Polygon(pairs, srid=4326)
        if srid != 4326:
            srs_to = SpatialReference(srid)
            srs_4326 = SpatialReference(4326)
            trans = CoordTransform(srs_4326, srs_to)
            geom.transform(trans)
        return geom

    def _geom_filters(self, qs):
        in_bbox = self.request.query_params.get('in_bbox', None)
        if in_bbox:
            poly__bboverlaps = '%s__bboverlaps' % self.layer.geom_field
            qs = qs.filter(**{poly__bboverlaps: self.bbox2wkt(
                in_bbox, self.layer.srid)})
        intersects = self.request.query_params.get('intersects', None)
        if intersects:
            poly__intersects = '%s__intersects' % self.layer.geom_field
            qs = qs.filter(**{poly__intersects: self.geom_from_intersects_param(intersects, self.layer.srid)})
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
                qs = qs.filter(reduce(OR, lst))  # noqa: E0602
        return qs

    def _get_queryset(self):
        qs = self.model.objects.all()
        qs = self._fullsearch_filters(qs)
        qs = self._geom_filters(qs)
        qs = self._virtual_fields_get_queryset(qs)
        model_filter = filterset_factory(self.model, self.filter_fields, self._virtual_fields)
        qs = model_filter(data=self.request.query_params, queryset=qs)
        qs = qs.filter()
        return qs

    def get_queryset(self):
        qs = None
        try:
            qs = self._get_queryset()
        except Exception:
            qs = self.model.objects_default.none()
        return qs

    def get_pagination_class(self, layer):
        page_size = layer.get_page_size()
        max_page_size = layer.get_max_page_size()
        if not layer.allow_page_size_0 and self.request.GET.get('page_size', page_size) == '0':
            raise PageSize0NotAllowedException()
        if self.request.GET.get('page_size', page_size) != '0':
            if self.layer.geom_field is None:
                return create_json_pagination_class(page_size=page_size, max_page_size=max_page_size)
            else:
                return create_geojson_pagination_class(page_size=page_size, max_page_size=max_page_size)

    # def delete_multiple(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     queryset.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def file_value(self, request, *args, **kwargs):
        attribute = kwargs['attribute']
        if attribute not in list(self._fields.keys()):
            raise Http404
        filter = {
            self.lookup_field: kwargs['pk'],
        }
        obj = get_object_or_404(self.model, **filter)
        file = getattr(obj, attribute)
        full_path = file.path
        fd = open(full_path, 'rb')
        file_mime = mimetypes.guess_type(file.name.split('/')[-1])
        response = FileResponse(fd, content_type=file_mime)
        patch_response_headers(response, cache_timeout=60 * 60 * 24 * 7)
        return response

    @action(detail=True, methods=['get'])
    def thumbnail_value(self, request, *args, **kwargs):
        attribute = kwargs['attribute']
        if attribute not in list(self._fields.keys()):
            raise Http404
        filter = {
            self.lookup_field: kwargs['pk'],
        }
        obj = get_object_or_404(self.model, **filter)
        file = getattr(obj, attribute)
        thumbnail = file.storage.get_thumbnail(file.name, create=True)
        full_path = thumbnail['path']
        fd = open(full_path, 'rb')
        file_mime = mimetypes.guess_type(file.name.split('/')[-1])
        response = FileResponse(fd, content_type=file_mime)
        patch_response_headers(response, cache_timeout=60 * 60 * 24 * 7)
        return response

    class Meta:
        filter_overrides = ['geom']


class DBLayerContentBulkViewSet(DBLayerContentViewSetMixin, views.APIView):
    ERROR_NOT_EXIST = 'ERROR_NOT_EXIST'
    ERROR_ON_SAVE = 'ERROR_ON_SAVE'

    csrf_exempt = True
    permission_classes = (BulkDBLayerIsValidUser,)
    queryset = []
    model = None

    def __init__(self, *args, **kwargs):
        self._fields = {}
        self.opened_files = []
        self.created_objects = []
        self.original_updated_objects = {}
        self.updated_objects = []
        self.user_assets = []
        self.readonly_fields = []
        self._to_do = []

    @giscube_transaction_cache_response()
    def dispatch(self, request, *args, **kwargs):
        self.layer = DataBaseLayer.objects.get(name=kwargs['name'])
        self.model = create_dblayer_model(self.layer)
        self.lookup_field = self.layer.pk_field
        self.geom_field = self.layer.geom_field
        self._fields = {}
        for field in self.layer.fields.filter(enabled=True):
            self._fields[field.name] = {}
            if field.readonly is True:
                self.readonly_fields.append(field.name)
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
            item = self.get_properties(item)
            for field in image_fields:
                if field in item:
                    item[field] = self.to_image(field, item[field])

    def clean_opened_files(self):
        for file in self.opened_files:
            try:
                file.close()
            except Exception as e:
                if settings.DEBUG:
                    logger.warning(e)

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
        Serializer = self.get_model_serializer_class()
        add_serializers = []
        for i, item in enumerate(items):
            serializer = Serializer(data=item, context={'request': self.request})
            if serializer.is_valid():
                add_serializers.append(serializer)
            else:
                return {i: serializer.errors}

        for i, serializer in enumerate(add_serializers):
            try:
                self.created_objects.append(serializer.save())
            except Exception:
                self.created_objects.append(serializer.instance)
                return {i: self.ERROR_ON_SAVE}

    def add_result(self, result):
        result['ADD'] = []
        for obj in self.created_objects:
            result['ADD'].append({self.lookup_field: getattr(obj, self.lookup_field)})

    def get_lookup_field_value(self, data):
        if 'properties' in data and isinstance(data['properties'], dict):
            if 'id' in data:
                return data['id']
            # Case: ADD - code is used as primary key in geojson
            elif self.lookup_field in data['properties']:
                return data['properties'][self.lookup_field]
        # Case using normal pk, pk key doesn't exist in ADD
        if self.lookup_field in data:
            return data[self.lookup_field]

    def get_properties(self, data):
        if 'properties' in data and isinstance(data['properties'], dict):
            new_data = data['properties']
            if self.lookup_field not in new_data:
                pk = self.get_lookup_field_value(data)
                # Case ADD using normal as pk, pk key doesn't exist
                if pk:
                    new_data[self.lookup_field] = pk
            return new_data
        return data

    def update(self, items):
        self.apply_widgets(items)
        Serializer = self.get_model_serializer_class()
        update_serializers = []
        for i, item in enumerate(items):
            filter = {}
            filter[self.lookup_field] = self.get_lookup_field_value(item)
            obj = self.model.objects.filter(**filter).first()
            if obj is None:
                return {i: self.ERROR_NOT_EXIST}

            self.original_updated_objects[list(filter.values())[0]] = model_to_dict(obj, exclude=['pk'])
            serializer = Serializer(instance=obj, data=item, partial=True, context={'request': self.request})
            if serializer.is_valid():
                update_serializers.append(serializer)
            else:
                return {i: serializer.errors}

        for i, serializer in enumerate(update_serializers):
            try:
                self.updated_objects.append(serializer.save())
            except Exception:
                self.updated_objects.append(serializer.instance)
                return {i: self.ERROR_ON_SAVE}

    def delete(self, items):
        filter = {}
        filter['%s__in' % self.lookup_field] = items
        qs = self.get_queryset().filter(**filter)
        image_fields = self._image_fields
        for item in qs:
            for field in image_fields:
                file = getattr(item, field, None)
                if file is not None:
                    self._to_do.append(lambda: file.delete(save=False))
            item.delete()

    def delete_user_assets(self):
        if len(self.user_assets) > 0:
            user_assets = UserAsset.objects.filter(file__in=self.user_assets)
            for asset in user_assets:
                asset.delete()

    def post(self, request, name):
        data = request.data
        errors = {}
        result = {}

        # TODO: schema
        self.layer.db_connection.get_connection()
        conn = self.layer.db_connection.connection_name()
        autocommit = transaction.get_autocommit(using=conn)
        transaction.set_autocommit(False, using=conn)

        if 'ADD' in data and len(data['ADD']) > 0:
            add_errors = self.add(data['ADD'])
            if add_errors:
                errors['ADD'] = add_errors

        if len(list(errors.keys())) == 0 and 'UPDATE' in data and len(data['UPDATE']) > 0:
            update_errors = self.update(data['UPDATE'])
            if update_errors:
                errors['UPDATE'] = update_errors

        # TODO: catch and raise delete errors
        if len(list(errors.keys())) == 0 and 'DELETE' in data and len(data['DELETE']) > 0:
            try:
                self.delete(data['DELETE'])
            except Exception:
                errors['DELETE'] = ['Unknown reason']

        if len(list(errors.keys())) > 0:
            response_status = status.HTTP_400_BAD_REQUEST
            self.undo()
            transaction.rollback(using=conn)
            result = errors
        else:
            response_status = status.HTTP_200_OK
            transaction.commit(using=conn)
            self.execute_to_do()
            self.delete_user_assets()
            self.add_result(result)

        transaction.set_autocommit(autocommit, using=conn)

        return Response(result, status=response_status)

    def execute_to_do(self):
        for x in self._to_do:
            x()
