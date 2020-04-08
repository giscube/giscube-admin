import time

import requests

from requests.exceptions import ConnectionError

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.generic import View

from imageserver.models import Service


class ImageserverProxy(View):
    # TODO: Refactor using giscube.wms_proxy.WMSProxy
    def get(self, request, service_name):
        service = get_object_or_404(Service, name=service_name, active=True)
        if service.visibility == 'private' and not request.user.is_authenticated:
            return HttpResponseForbidden()

        server_url = settings.GISCUBE_IMAGE_SERVER_URL
        meta = request.META.get('QUERY_STRING', '?')
        mapfile = "map=%s" % service.mapfile_path
        url = "%s?%s&%s" % (server_url, meta, mapfile)

        retrying = False
        response = None
        for retry in range(5):
            try:
                r = requests.get(url)
                content_type = r.headers['content-type']
                if content_type == 'text/xml' and \
                        'ServiceException' in r.content:
                    print('===================================================')
                    print(r.content)
                if content_type == 'text/xml':
                    print('********************')
                    print(r.content)
                response = HttpResponse(r.content,
                                        content_type=content_type)
                response.status_code = r.status_code
                break
            except ConnectionError as e:
                print(e)

                if retrying:
                    # calm down
                    print('retry number %s' % retry)
                    time.sleep(1)
                else:
                    retrying = True

        if not response:
            response = HttpResponse('Unable to contact server')
            response.status_code = 500

        return response
