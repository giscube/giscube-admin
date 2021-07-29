import logging
import os

import requests

from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.cache import patch_response_headers
from django.views.generic import View

from giscube.tilecache.caches import GiscubeServiceCache
from giscube.tilecache.image import tile_cache_image
from giscube.tilecache.proj import GoogleProjection
from giscube.utils import get_service_wms_bbox
from giscube.views_mixins import WMSProxyBufferView
from giscube.views_utils import web_map_view

from .models import Service


logger = logging.getLogger(__name__)


class ServiceMixin:
    model = Service

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
            filter_user = Q(user_permissions__user=self.request.user) & Q(
                user_permissions__can_view=True)
            qs = qs.filter(
                filter_anonymous | filter_authenticated_user_view | filter_user | filter_group).distinct()

        return qs

    def get_queryset_can_write(self, *args, **kwargs):
        qs = self.model.objects.filter(active=True)
        filter_anonymous = Q(anonymous_write=True)

        if self.request.user.is_anonymous:
            qs = qs.filter(filter_anonymous)
        else:
            self.user_groups = self.request.user.groups.values_list('name', flat=True)
            filter_authenticated_user_write = Q(authenticated_user_write=True)
            filter_group = (
                Q(group_permissions__group__name__in=self.user_groups) & Q(group_permissions__can_write=True))
            filter_user = Q(user_permissions__user=self.request.user) & Q(
                user_permissions__can_write=True)
            qs = qs.filter(
                filter_anonymous | filter_authenticated_user_write | filter_user | filter_group).distinct()

        return qs


class QGISServerWMSView(ServiceMixin, WMSProxyBufferView):
    def get_wms_buffer_enabled(self):
        return self.service.wms_buffer_enabled

    def get_wms_buffer_size(self):
        return self.service.wms_buffer_size or ''

    def get_wms_tile_sizes(self):
        return (self.service.wms_tile_sizes or '').splitlines()

    def is_request_parameter_allowed(self, parameters):
        fixed = {key.upper(): value.upper() for key, value in parameters.items()}
        if fixed.get('REQUEST') == 'GETFEATUREINFO' and not self.service.wms_getfeatureinfo_enabled:
            return False
        return True

    def get(self, request, service_name):
        self.service = get_object_or_404(self.get_queryset(), name=service_name)

        if not self.is_request_parameter_allowed(request.GET):
            return HttpResponseForbidden()

        return super().get(request)

    def post(self, request, service_name):
        self.service = get_object_or_404(self.get_queryset_can_write(), name=service_name)

        if not self.is_request_parameter_allowed(request.POST):
            return HttpResponseForbidden()

        url = self.build_url(request)
        return requests.post(url, data=request.body)

    def build_url(self, request):
        meta = request.META.get('QUERY_STRING', '')
        url = "%s&%s" % (self.service.service_internal_url, meta)
        return url


class QGISServerTileCacheView(ServiceMixin, View):
    def get(self, request, service_name):
        service = get_object_or_404(self.get_queryset(), name=service_name)
        data = {}
        if service.tilecache_enabled:
            data.update(
                {
                    'bbox': service.tilecache_bbox,
                    'min_zoom': service.tilecache_minzoom_level,
                    'max_zoom': service.tilecache_maxzoom_level
                }
            )
        return JsonResponse(data)


class QGISServerTileCacheTilesView(ServiceMixin, View):
    def build_url(self, service):
        url = service.service_internal_url
        if service.tilecache_transparent:
            url = '%s&transparent=True' % url
        return url

    def get(self, request, service_name, z, x, y, image_format='png'):
        service = get_object_or_404(self.get_queryset(), name=service_name, tilecache_enabled=True)

        if z < service.tilecache_minzoom_level or z > service.tilecache_maxzoom_level:
            return HttpResponseBadRequest()

        bbox = self.tile2bbox(z, x, y)
        layers = os.path.splitext(os.path.basename(service.project_file.name))[0]
        tile_options = {
            'url': self.build_url(service),
            'layers': layers,
            'xyz': [z, x, y],
            'bbox': bbox,
            'srs': 'EPSG:3857'
        }

        buffer = [0, 0]
        if service.wms_buffer_enabled:
            buffer = list(map(int, service.wms_buffer_size.split(',')))
        cache = GiscubeServiceCache(service)
        image = tile_cache_image(tile_options, buffer, cache)
        response = HttpResponse(image, content_type='image/%s' % image_format)
        patch_response_headers(response, cache_timeout=60 * 60 * 24 * 7)
        response.status_code = 200
        return response

    def tile2bbox(self, z, x, y):
        proj = GoogleProjection(256, [z])
        bbox = proj.tile_bbox((z, x, y))
        return proj.project(bbox[:2]) + proj.project(bbox[2:])


class QGISServerMapViewerView(ServiceMixin, View):
    def get(self, request, service_name):
        service = get_object_or_404(self.get_queryset(), name=service_name)

        layers = []
        layers.append(
            {
                'name': '%s (WMS)' % (service.title or service.name),
                'type': 'wms',
                'layers': service.default_layer,
                'url': reverse('qgisserver', args=(service.name, '',)),
                'transparent': service.tilecache_enabled and service.tilecache_transparent
            }
        )
        if service.tilecache_enabled:
            layers.append(
                {
                    'name': '%s (Tile Cache)' % (service.title or service.name),
                    'type': 'tile',
                    'url': '%s{z}/{x}/{y}.png' % reverse('qgisserver-tilecache', args=(service.name,))
                }
            )
        extra_context = {
            'title': service.title or service.name,
            'layers': layers
        }
        bbox = get_service_wms_bbox(service.service_internal_url)
        if bbox:
            extra_context['bbox'] = list(bbox)

        return web_map_view(request, extra_context)
