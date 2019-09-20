import logging

import requests

from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from giscube.views_mixins import WMSProxyBufferMixin

from .models import Service


logger = logging.getLogger(__name__)


class QGISProxy(WMSProxyBufferMixin):
    def get_wms_buffer_enabled(self):
        return self.service.wms_buffer_enabled

    def get_wms_buffer_size(self):
        return self.service.wms_buffer_size or ''

    def get_wms_tile_sizes(self):
        return (self.service.wms_tile_sizes or '').splitlines()

    def do_get(self, request, service_name):
        service = get_object_or_404(Service, name=service_name, active=True)
        self.service = service
        if service.visibility == 'private' and not request.user.is_authenticated:
            return HttpResponseForbidden()

        buffered_image = self.get_buffered_image()
        if buffered_image:
            return buffered_image

        url = self.build_url(request)
        return requests.get(url)

    def do_post(self, request, service_name):
        service = get_object_or_404(Service, name=service_name, active=True)
        if service.visibility == 'private' and not request.user.is_authenticated:
            return HttpResponseForbidden()
        url = self.do_build_url(request, service_name)
        return requests.post(url, data=request.body)

    def build_url(self, request):
        server_url = settings.GISCUBE_QGIS_SERVER_URL
        meta = request.META.get('QUERY_STRING', '?')
        mapfile = "map=%s" % self.service.project_file.path
        url = "%s?%s&%s" % (server_url, meta, mapfile)
        return url
