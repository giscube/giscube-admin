import logging

import requests

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.cache import patch_response_headers
from django.views.generic import View

from giscube.tilecache.image import tile_cache_image


logger = logging.getLogger(__name__)


class ProxyMixin:
    def _do_call(self, call_type, request, *args, **kwargs):
        try:
            response = call_type(*args, **kwargs)
        except Exception as e:
            return self._process_remote_error(request, e)
        else:
            return self._process_remote_response(response)

    def get(self, request, *args, **kwargs):
        return self._do_call(requests.get, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self._do_call(requests.post, request, *args, **kwargs)

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


class WMSProxyMixin(ProxyMixin):
    def param_get(self, data, param, default=None):
        return data.get(param.lower(), data.get(param.upper(), default))

    def getmap(self, request):
        url = self.build_url(request)
        return super().get(request, url=url)

    def getcapabilities(self, request):
        url = self.build_url(request)
        return super().get(request, url=url)

    def getlegendgraphic(self, request):
        url = self.build_url(request)
        return super().get(request, url=url)

    def getfeatureinfo(self, request):
        url = self.build_url(request)
        return super().get(request, url=url)

    def get(self, request):
        wms_service = self.param_get(request.GET, 'service', '').lower()
        wms_request = self.param_get(request.GET, 'request', '').lower()
        if wms_service == 'wms':
            if wms_request in ('getmap', 'getcapabilities', 'getlegendgraphic', 'getfeatureinfo'):
                return getattr(self, wms_request)(request)
        return HttpResponseBadRequest()


class WMSProxyBufferMixin(WMSProxyMixin):
    def get_wms_buffer_enabled(self):
        raise NotImplementedError('To be implemented')

    def get_wms_buffer_size(self):
        raise NotImplementedError('To be implemented')

    def get_wms_tile_sizes(self):
        raise NotImplementedError('To be implemented')

    def get_buffered_image(self):
        request = self.request
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

        url = self.build_url(request)
        size_matches = False
        if self.get_wms_tile_sizes():
            size_requested = '%s,%s' % (width, height)
            for line in self.get_wms_tile_sizes():
                if line == size_requested:
                    size_matches = True
                    break
        if len(bbox) == 4 and size_matches:
            image = None
            wms_options = {
                'url': url,
                'layers': layers,
                'bbox': bbox,
                'width': width,
                'height': height,
                'dpi': dpi,
                'srs': srs
            }
            buffer = list(map(int, self.get_wms_buffer_size().split(',')))
            try:
                image = tile_cache_image(wms_options, buffer)
            except Exception as e:
                msg = 'wms request is not a tile: %s' % e
                print(msg)
                if settings.DEBUG:
                    raise Exception(msg)
            else:
                response = HttpResponse(image, content_type='image/png')
                patch_response_headers(response, cache_timeout=60 * 60 * 24 * 7)
                response.status_code = 200
                return response

    def getmap(self, request):
        response = None
        if self.get_wms_buffer_enabled():
            response = self.get_buffered_image()
        if response is None:
            response = super().getmap(request)
        return response


class WMSProxyBufferView(WMSProxyBufferMixin, View):
    pass
