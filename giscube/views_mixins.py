import logging

import requests

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View

logger = logging.getLogger(__name__)


class WMSProxyMixin(View):
    def do_get(self, request, service_name):
        raise NotImplementedError('To be implemented')

    def _do_call(self, call_type, request, service_name):
        try:
            response = call_type(request, service_name)
        except Exception as e:
            return self._process_remote_error(request, e)
        else:
            if isinstance(response, HttpResponse):
                return response
            else:
                return self._process_remote_response(response)

    def get(self, request, service_name):
        return self._do_call(self.do_get, request, service_name)

    def do_post(self, request, service_name):
        raise NotImplementedError('To be implemented')

    def post(self, request, service_name):
        return self._do_call(self.do_post, request, service_name)

    def build_url(self, request, service_name):
        raise NotImplementedError('To be implemented')

    def _process_remote_response(self, r):
        content_type = r.headers['content-type']
        response = HttpResponse(r.content, content_type=content_type)
        response.status_code = r.status_code
        return response

    def _process_remote_error(self, request, e):
        content = b''
        if settings.DEBUG:
            import traceback
            try:
                raise e
            except Exception:
                content = traceback.format_exc()
                print(content)

        if isinstance(e, (OSError, requests.ConnectTimeout, requests.ReadTimeout, requests.Timeout)):
            logger.warning('Request to the underlying WMS service failed. Timeout.')
            return HttpResponse(content, status=504)
        else:
            logging.warning(e, exc_info=True)
            return HttpResponse('Unable to contact server', status=502)


class WMSBufferMixin(object):
    pass


class WMSProxyBufferMixin(WMSProxyMixin, WMSBufferMixin):
    def param_get(self, data, param, default=None):
        return data.get(param.lower(), data.get(param.upper(), default))

    def get_wms_buffer_enabled(self):
        raise NotImplementedError('To be implemented')

    def get_wms_buffer_size(self):
        raise NotImplementedError('To be implemented')

    def get_wms_tile_sizes(self):
        raise NotImplementedError('To be implemented')

    def get_buffered_image(self):
        if self.get_wms_buffer_enabled():
            request = self.request
            wms_service = self.param_get(request.GET, 'service', '').lower()
            wms_request = self.param_get(request.GET, 'request', '').lower()
            layers = self.param_get(request.GET, 'layers')
            srs = self.param_get(request.GET, 'srs')
            bbox = self.param_get(request.GET, 'bbox', '')
            if bbox:
                try:
                    bbox = list(map(float, bbox.split(',')))
                except Exception:
                    bbox = []
            width = self.param_get(request.GET, 'width', '')
            height = self.param_get(request.GET, 'height', '')
            dpi = self.param_get(request.GET, 'dpi', '')

            size_matches = False
            if self.get_wms_tile_sizes():
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
                    print('wms request is not a tile: %s' % e)
