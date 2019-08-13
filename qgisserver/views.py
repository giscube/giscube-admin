import logging

import requests

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.generic import View

from qgisserver.models import Service


logger = logging.getLogger(__name__)


def param_get(data, param, default=None):
    return data.get(param.lower(), data.get(param.upper(), default))


class QGISProxy(View):
    def get(self, request, service_name):
        service = get_object_or_404(Service, name=service_name, active=True)
        if service.visibility == 'private' and not request.user.is_authenticated:
            return HttpResponseForbidden()

        if service.wms_buffer_enabled:
            wms_service = param_get(request.GET, 'service', '').lower()
            wms_request = param_get(request.GET, 'request', '').lower()
            layers = param_get(request.GET, 'layers')
            srs = param_get(request.GET, 'srs')
            bbox = param_get(request.GET, 'bbox', '')
            if bbox:
                try:
                    bbox = list(map(float, bbox.split(',')))
                    print('BBOX', bbox)
                except Exception:
                    bbox = []
            width = param_get(request.GET, 'width', '')
            height = param_get(request.GET, 'height', '')
            dpi = param_get(request.GET, 'dpi', '')

            size_matches = True
            if service.wms_tile_sizes:
                size_matches = False
                size_requested = '%s,%s' % (width, height)
                for line in service.wms_tile_sizes.splitlines():
                    if line == size_requested:
                        size_matches = True
                        break

            if wms_service == 'wms' and wms_request == 'getmap' and \
                    len(bbox) == 4 and size_matches:

                from TileCache.Layers.WMS import WMS
                from TileCache.Caches.Test import Test as NoCache

                url = self._build_url(request, service_name)

                wms = WMS(layers, url=url, srs=srs, levels=30,
                          spherical_mercator='true')
                wms.cache = NoCache()
                wms.size = list(map(int, [width, height]))
                try:
                    tile = wms.getTile(bbox)

                    wms.metaSize = (1, 1)
                    buffer = list(map(int, service.wms_buffer_size.split(',')))

                    # if dpi is specified, adjust buffer
                    if dpi:
                        ratio = float(dpi) / 91.0
                        buffer = [int(x * ratio) for x in buffer]

                    wms.metaBuffer = buffer
                    metatile = wms.getMetaTile(tile)
                    image = wms.renderMetaTile(metatile, tile)

                    response = HttpResponse(image, content_type='image/png')
                    response.status_code = 200
                    return response
                except Exception as e:
                    # wms request is not a tile
                    print('wms request is not a tile: %s' % e)

        url = self._build_url(request, service_name)

        r = None
        response = None
        try:
            r = requests.get(url)
        except Exception as e:
            print(e)

        response = self._process_remote_response(r)
        return response

    def post(self, request, service_name):
        url = self._build_url(request, service_name)

        response = None
        try:
            r = requests.post(url, data=request.body)
        except Exception as e:
            print(e)

        response = self._process_remote_response(r)
        return response

    def _build_url(self, request, service_name):
        service = get_object_or_404(Service, name=service_name)
        server_url = settings.GISCUBE_QGIS_SERVER_URL
        meta = request.META.get('QUERY_STRING', '?')
        mapfile = "map=%s" % service.project_file.path
        url = "%s?%s&%s" % (server_url, meta, mapfile)
        return url

    def _process_remote_response(self, r):
        if r:
            content_type = r.headers['content-type']
            response = HttpResponse(r.content,
                                    content_type=content_type)
            response.status_code = r.status_code
        else:
            logger.warning(
                'Request to the underlying WMS service failed',
                extra={
                    'url': r.url,
                    'status_code': r.status_code,
                    'content': str(r.content),
                },
                exc_info=True,
            )

            response = HttpResponse('Unable to contact server')
            response.status_code = 500

        return response
