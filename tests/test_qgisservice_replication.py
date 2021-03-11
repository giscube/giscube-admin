import base64
import json

from pathlib import Path

from django.core.files import File
from django.urls import reverse

from rest_framework import status

from qgisserver.models import Service
from tests.common import BaseTest


class QGISServiceReplicationTestCase(BaseTest):
    def test_status_ok(self):
        self.login_superuser()
        url = reverse('qgisserver_service-list')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_create(self):
        self.login_superuser()
        url = reverse('qgisserver_service-list')
        project_file_path = 'tests/files/project1.qgs'
        file_name = Path(project_file_path).name
        with open(project_file_path, 'rb') as project_file:
            project_content = base64.b64encode(project_file.read()).decode('utf-8')
            data = {
                'name': 'test-create',
                'active': True,
                'user_permissions': [
                    {
                        'user': {
                            'username': 'peter',
                            'email': 'peter@gmail.com'
                        },
                        'can_view': True,
                        'can_write': True
                    }
                ],
                'group_permissions': [
                    {
                        'group': {
                            'name': 'admins'
                        },
                        'can_view': True,
                        'can_write': True
                    }
                ],
                'project_file': f'data:text/xml;charset=utf8-8;name={file_name};base64,{project_content}'
            }
            response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        result = response.json()
        self.assertEqual(result['name'], data['name'])
        self.assertEqual(len(result['user_permissions']), 1)
        self.assertEqual(result['user_permissions'][0]['user']['username'], 'peter')
        self.assertTrue(result['user_permissions'][0]['can_view'])
        self.assertTrue(result['user_permissions'][0]['can_write'])
        self.assertEqual(len(result['group_permissions']), 1)
        self.assertEqual(result['group_permissions'][0]['group']['name'], 'admins')
        self.assertTrue(result['group_permissions'][0]['can_view'])
        self.assertTrue(result['group_permissions'][0]['can_write'])

    def test_update(self):
        with open('tests/files/project1.qgs', 'rb') as f:
            Service.objects.create(
                name='project-1',
                active=False,
                project_file=File(f, name='project1.qgs')
            )

        self.login_superuser()
        url = reverse('qgisserver_service-list')
        project_file_path = 'tests/files/project2.qgs'
        file_name = Path(project_file_path).name
        with open(project_file_path, 'rb') as project_file:
            project_content = base64.b64encode(project_file.read()).decode('utf-8')
            data = {
                'name': 'project-1',
                'active': True,
                'user_permissions': [
                    {
                        'user': {
                            'username': 'peter',
                            'email': 'peter@gmail.com'
                        },
                        'can_view': True,
                        'can_write': True
                    }
                ],
                'group_permissions': [
                    {
                        'group': {
                            'name': 'admins'
                        },
                        'can_view': True,
                        'can_write': True
                    }
                ],
                'project_file': f'data:text/xml;charset=utf8-8;name={file_name};base64,{project_content}'
            }
            response = self.client.put(url, data=json.dumps(data), content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
