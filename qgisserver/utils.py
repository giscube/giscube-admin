from __future__ import absolute_import, unicode_literals

import os
import requests
import tempfile
from celery import shared_task
import xml.etree.ElementTree as ET

from django.conf import settings
from django.urls import reverse


def patch_qgis_project(service):
    filename = service.project_file.path
    tree = ET.parse(filename)
    root = tree.getroot()
    properties = root.find('properties')
    wms_url = properties.find('WMSUrl')
    if wms_url is None:
        wms_url = ET.SubElement(properties, 'WMSUrl')
    giscube_url = getattr(settings, 'GISCUBE_URL', 'http://localhost:8080')
    wms_url.text = '%s/qgisserver/services/%s/' % (giscube_url, service.name)
    tree.write(filename)


def unique_service_directory(instance, filename):
    if not instance.service_path:
        path = os.path.join(settings.MEDIA_ROOT, instance._meta.app_label)
        path = os.path.abspath(path)
        if not os.path.exists(path):
            os.makedirs(path)
        pathname = tempfile.mkdtemp(prefix='%s_' % instance.name, dir=path)
        pathname = os.path.relpath(pathname, settings.MEDIA_ROOT)
        instance.service_path = pathname
    return os.path.join(instance.service_path, filename)


@shared_task
def update_external_service(service):
    from .models import Server
    from .serializers import ServiceSerializer

    # Generic configuration
    api_put_url = reverse('qgisserver_service-detail', args=[service.name])
    api_post_url = reverse('qgisserver_service-list')
    data = dict(ServiceSerializer(service).data)
    data['active'] = True

    for server in service.servers.filter(this_server=False):

        # Server configuration
        headers = {
            'Authorization': 'Bearer %s' % server.token
        }

        # Update or create server
        response = requests.put(
            server.url+api_put_url,
            data=data,
            headers=headers,
        )
        if response.status_code == 404:
            response = requests.post(
                server.url+api_post_url,
                data=data,
                headers=headers,
            )

        # TODO: handle other errors


@shared_task
def deactivate_services(service_name, server_pks):
    from .models import Server

    api_url = reverse('qgisserver_service-detail', args=[service_name])
    data = { 'active': False }

    for server in Server.objects.filter(pk__in=server_pks, this_server=False):
        # Server configuration
        headers = {
            'Authorization': 'Bearer %s' % server.token
        }
        requests.patch(server.url+api_url, data=data, headers=headers)

        # TODO: handle errors
