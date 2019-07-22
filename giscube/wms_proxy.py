import logging

import requests

from django.http import HttpResponse


logger = logging.getLogger(__name__)


def param_get(data, param, default=None):
    return data.get(param.lower(), data.get(param.upper(), default))


class WMSProxy(object):
    def __init__(self, service):
        self.service = service

    def build_url(self, request):
        raise NotImplementedError('To be implemented')

    def get_wms_buffer_enabled(self):
        raise NotImplementedError('To be implemented')

    def get_service_name(self, service):
        raise NotImplementedError('To be implemented')

    def get_wms_buffer_size(self):
        raise NotImplementedError('To be implemented')

    def get_wms_tile_sizes(self):
        raise NotImplementedError('To be implemented')

    def get(self, request):
        if self.get_wms_buffer_enabled():
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
            if self.get_wms_tile_sizes():
                size_matches = False
                size_requested = '%s,%s' % (width, height)
                for line in self.get_wms_tile_sizes():
                    if line == size_requested:
                        size_matches = True
                        break

            if wms_service == 'wms' and wms_request == 'getmap' and \
                    len(bbox) == 4 and size_matches:

                from TileCache.Layers.WMS import WMS
                from TileCache.Caches.Test import Test as NoCache

                url = self.build_url(request)
                wms = WMS(layers, url=url, srs=srs, levels=30, spherical_mercator='true')
                wms.cache = NoCache()
                wms.size = list(map(int, [width, height]))
                try:
                    tile = wms.getTile(bbox)

                    wms.metaSize = (1, 1)
                    buffer = list(map(int, self.get_wms_buffer_size().split(',')))

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

        url = self.build_url(request)

        response = None
        try:
            r = requests.get(url)
        except Exception as e:
            print(e)

        response = self._process_remote_response(r)
        return response

    def post(self, request):
        url = self.build_url(request)
        response = None
        try:
            r = requests.post(url, data=request.body)
        except Exception as e:
            print(e)

        response = self._process_remote_response(r)
        return response

    def _process_remote_response(self, r):
        if r:
            content_type = r.headers['content-type']
            response = HttpResponse(r.content,
                                    content_type=content_type)
            response.status_code = r.status_code
        else:
            logger.error(r.url)
            print(r.content)
            response = HttpResponse('Unable to contact server')
            response.status_code = 500

        return response
