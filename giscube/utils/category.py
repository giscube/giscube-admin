from urllib.parse import urlencode

import requests

from django.conf import settings
from django.urls import reverse

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
        parameters = {'name': category.name.encode()}
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
