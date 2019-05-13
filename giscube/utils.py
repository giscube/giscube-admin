import os
import tempfile
from urllib.parse import urlencode

import requests

from django.conf import settings
from django.urls import reverse
from django.utils.module_loading import import_string
from django.utils.version import get_version as django_get_version

from rest_framework import status


def create_category(server_url, headers, data):
    category_list_url = reverse('api_v2_giscube_category-list').replace(settings.APP_URL, '')
    response = requests.post(
        '%s%s' % (server_url, category_list_url),
        headers=headers,
        json=data
    )
    if response.status_code == status.HTTP_201_CREATED:
        return response.json()


def get_or_create_category(server_url, headers, category):
    category_list_url = reverse('api_v2_giscube_category-list').replace(settings.APP_URL, '')

    # Search category
    if category is not None:
        parameters = {'name': category.name.encode}
        if category.parent is not None:
            parameters['parent__name'] = category.parent.name
        url = '%s?%s' % (category_list_url, urlencode(parameters))
        response = requests.get(
            '%s%s' % (server_url, url),
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            if len(result) > 0:
                return result[0]['id']

        # Create category
        data = {'parent': None, 'name': category.name}
        if category.parent is not None:
            parameters = {'name': category.name, 'parent__isnull': 'True'}
            url = '%s?%s' % (category_list_url, urlencode(parameters))
            response = requests.get(
                '%s%s' % (server_url, url),
                headers=headers
            )
            if response.status_code == 200:
                result = response.json()
                if len(result) == 0:
                    parent = create_category(server_url, headers, {'name': category.parent.name})
                    if parent is not None:
                        data['parent'] = parent['id']
                else:
                    data['parent'] = result[0]['id']

        result = create_category(server_url, headers, data)
        if result is not None:
            return result['id']


def get_version(version=None):
    if version is None:
        from . import VERSION as version

    return django_get_version(version)


def unique_service_directory(instance, filename=None):
    if not instance.service_path:
        path = os.path.join(settings.MEDIA_ROOT, instance._meta.app_label)
        path = os.path.abspath(path)
        if not os.path.exists(path):
            os.makedirs(path)
        pathname = tempfile.mkdtemp(prefix='%s_' % instance.name, dir=path)
        pathname = os.path.relpath(pathname, settings.MEDIA_ROOT)
        instance.service_path = pathname
    if filename:
        return os.path.join(instance.service_path, filename)
    else:
        return instance.service_path


def get_cls(key, default=None):
    value = getattr(settings, key, None)
    if type(value) is type:
        return value
    elif type(value) is tuple or type(value) is list:
        return tuple(import_string(p) for p in value if type(p) is str)
    elif type(value) is str:
        return import_string(value)
    else:
        return default
