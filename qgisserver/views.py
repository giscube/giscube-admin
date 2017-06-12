import os
import time
import subprocess
import logging

from django.views.generic import View
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings

import requests
from requests.exceptions import ConnectionError

from qgisserver.models import Service

logger = logging.getLogger(__name__)


class QGISProxy(View):
    def get(self, request, service_name):
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
        qserver_url = "http://localhost/fcgis/qgisserver/"
        meta = request.META.get('QUERY_STRING', '?')
        mapfile = "map=%s" % service.project.path
        url = "%s?%s&%s" % (qserver_url, meta, mapfile)
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
