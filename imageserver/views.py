import logging

import requests
from requests.structures import CaseInsensitiveDict

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse, QueryDict
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.cache import patch_response_headers
from django.views.generic import View

from giscube.permissions import PermissionQuerysetMixin
from giscube.tilecache.caches import GiscubeServiceCache
from giscube.tilecache.image import tile_cache_image
from giscube.tilecache.proj import GoogleProjection
from giscube.utils import get_service_wms_bbox
from giscube.views_mixins import WMSProxyView
from giscube.views_utils import web_map_view

from .models import Service


logger = logging.getLogger(__name__)


class ServiceMixin(PermissionQuerysetMixin):
    model = Service


class ImageServerWMSView(ServiceMixin, WMSProxyView):
    def get(self, request, service_name):
        self.service = get_object_or_404(self.get_queryset(), name=service_name)

        response = super().get(request)
        headers = getattr(response, '_headers', {})
        if 'content-type' in headers:
            content_type = None
            try:
                content_type = headers.get('content-type')[1]
            except Exception:
                pass
            if content_type == 'application/vnd.ogc.wms_xml; charset=UTF-8':
                response['Content-Type'] = 'text/xml; charset=UTF-8'
        return response

    def post(self, request, service_name):
        self.service = get_object_or_404(self.get_queryset_can_write(), name=service_name)
        url = self.build_url(request)
        return requests.post(url, data=request.body)

    def build_url(self, request):
        meta = request.META.get('QUERY_STRING', '')
        version = CaseInsensitiveDict(request.GET).get('version')
        if version is None:
            querydict = QueryDict(meta, mutable=True)
            querydict['version'] = settings.IMAGE_SERVER_DEFAULT_WMS_VERSION
            meta = querydict.urlencode()

        url = "%s&%s" % (self.service.service_internal_url, meta)
        return url


class ImageServerTileCacheView(ServiceMixin, View):
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


class ImageServerTileCacheTilesView(ServiceMixin, View):
    def build_url(self, service):
        return service.service_internal_url

    def get(self, request, service_name, z, x, y, image_format='png'):
        service = get_object_or_404(self.get_queryset(), name=service_name, tilecache_enabled=True)

        if z < service.tilecache_minzoom_level or z > service.tilecache_maxzoom_level:
            return HttpResponseBadRequest()

        bbox = self.tile2bbox(z, x, y)
        tile_options = {
            'url': self.build_url(service),
            'layers': ','.join(service.servicelayer_set.all().values_list('layer__name', flat=True)),
            'xyz': [z, x, y],
            'bbox': bbox,
            'srs': 'EPSG:3857'
        }

        buffer = [0, 0]
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


class ImageServerMapViewerView(ServiceMixin, View):
    def get(self, request, service_name):
        service = get_object_or_404(self.get_queryset(), name=service_name)

        layers = []
        layers.append(
            {
                'name': '%s (WMS)' % (service.title or service.name),
                'type': 'wms',
                'layers': service.default_layer,
                'url': reverse('imageserver', args=(service.name, '',))
            }
        )
        if service.tilecache_enabled:
            layers.append(
                {
                    'name': '%s (Tile Cache)' % (service.title or service.name),
                    'type': 'tile',
                    'url': '%s{z}/{x}/{y}.png' % reverse('imageserver-tilecache', args=(service.name,))
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
