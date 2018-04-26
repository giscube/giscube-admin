import logging

from django.views.generic import View
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings

import requests

from qgisserver.models import Service

logger = logging.getLogger(__name__)


class QGISProxy(View):
    def get(self, request, service_name):
        service = get_object_or_404(Service, name=service_name)

        if service.wms_buffer_enabled:
            wms_service = request.GET.get('service', '').lower()
            wms_request = request.GET.get('request', '').lower()
            layers = request.GET.get('layers')
            srs = request.GET.get('srs')
            bbox = request.GET.get('bbox', '')
            bbox = map(float, bbox.split(','))
            width = request.GET.get('width', '')
            height = request.GET.get('height', '')
            dpi = request.GET.get('dpi', '')

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
                wms.size = map(int, [width, height])
                tile = wms.getTile(bbox)

                wms.metaSize = (1, 1)
                buffer = map(int, service.wms_buffer_size.split(','))

                # if dpi is specified, adjust buffer
                if dpi:
                    ratio = float(dpi) / 91.0
                    buffer = map(lambda x: int(x * ratio), buffer)

                wms.metaBuffer = buffer
                metatile = wms.getMetaTile(tile)
                image = wms.renderMetaTile(metatile, tile)

                response = HttpResponse(image, content_type='image/png')
                response.status_code = 200
                return response

        url = self._build_url(request, service_name)

        response = None
        try:
            r = requests.get(url)
        except Exception, e:
            print e

        response = self._process_remote_response(r)
        return response

    def post(self, request, service_name):
        url = self._build_url(request, service_name)

        response = None
        try:
            r = requests.post(url, data=request.body)
        except Exception, e:
            print e

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
            logger.error(r.url)
            print r.content
            response = HttpResponse('Unable to contact server')
            response.status_code = 500

        return response
