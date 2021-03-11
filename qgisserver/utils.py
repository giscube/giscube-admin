import base64
import json
import os

from pathlib import Path
from xml.etree import ElementTree as ET

import requests

from celery import shared_task

from django.conf import settings
from django.urls import reverse

from rest_framework import status

from giscube.utils import unique_service_directory as giscube_unique_service_directory
from giscube.utils import url_slash_join


def patch_qgis_project(service):
    file_path = service.project_file.path
    tree = ET.parse(file_path)
    root = tree.getroot()
    properties = root.find('properties')

    wms_url = properties.find('WMSUrl')
    if wms_url is None:
        wms_url = ET.SubElement(properties, 'WMSUrl')
        wms_url.set('type', 'QString')
    giscube_url = getattr(settings, 'GISCUBE_URL', 'http://localhost:8080')
    wms_url.text = url_slash_join(giscube_url, '/qgisserver/services/%s/' % service.name)

    project_file = os.path.basename(file_path)
    filename, _ = os.path.splitext(project_file)

    wms_service_capabilities = properties.find('WMSServiceCapabilities')
    if wms_service_capabilities is None:
        wms_service_capabilities = ET.SubElement(properties, 'WMSServiceCapabilities')
        wms_service_capabilities.set('type', 'bool')
    wms_service_capabilities.text = 'true'

    wms_root_name = properties.find('WMSRootName')
    if wms_root_name is None:
        wms_root_name = ET.SubElement(properties, 'WMSRootName')
        wms_root_name.set('type', 'QString')
    wms_root_name.text = filename

    tree.write(file_path)


def unique_service_directory(instance, filename=None):
    return giscube_unique_service_directory(instance, filename, append_object_name=False)


@shared_task
def update_external_service(service_pk):
    from giscube.utils import get_or_create_category

    from .models import Service
    from .serializers import ServiceSerializer

    service = Service.objects.get(pk=service_pk)
    # Generic configuration
    api_put_url = reverse('qgisserver_service-detail', args=[service.name])
    api_put_url = api_put_url.replace(settings.APP_URL, '')
    api_post_url = reverse('qgisserver_service-list')
    api_post_url = api_post_url.replace(settings.APP_URL, '')
    data = dict(ServiceSerializer(service).data)
    data['active'] = True

    headers = {'Content-type': 'application/json'}

    file_name = os.path.basename(service.project_file.name)
    file_path = os.path.join(settings.MEDIA_ROOT, service.project_file.name)

    for server in service.servers.filter(this_server=False):
        if not server.url:
            continue

        # Server configuration
        headers['Authorization'] = 'Bearer %s' % server.token

        # Category
        data['category'] = get_or_create_category(server.url, headers, service.category)

        # Service
        file_name = Path(file_path).name
        with open(file_path, 'rb') as project_file:
            project_content = base64.b64encode(project_file.read()).decode('utf-8')
            data['project_file'] = f'data:text/xml;charset=utf8-8;name={file_name};base64,{project_content}'

        # Update or create server
        response = requests.put(
            '%s%s' % (server.url, api_put_url),
            data=json.dumps(data),
            headers=headers
        )

        if response.status_code == 404:
            response = requests.post(
                '%s%s' % (server.url, api_post_url),
                data=json.dumps(data),
                headers=headers
            )
            project_file.close()
            if response.status_code != status.HTTP_201_CREATED:
                raise Exception('SERVER response status [%s]' % response.status_code)

        # TODO: handle other errors


@shared_task
def deactivate_services(service_name, server_pks):
    from .models import Server

    api_url = reverse('qgisserver_service-detail', args=[service_name])
    data = {'active': False}

    for server in Server.objects.filter(pk__in=server_pks, this_server=False):
        if not server.url:
            continue

        # Server configuration
        headers = {
            'Authorization': 'Bearer %s' % server.token
        }
        requests.patch(server.url + api_url, data=data, headers=headers)

        # TODO: handle errors
