import base64
import json

from pathlib import Path

from django.contrib.auth.models import Group, User
from django.core.files import File
from django.urls import reverse

from rest_framework import status

from qgisserver.models import Service, ServiceGroupPermission, ServiceUserPermission
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

    def test_update_status_ok(self):
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

    def test_update_project(self):
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
                'user_permissions': [],
                'group_permissions': [],
                'project_file': f'data:text/xml;charset=utf8-8;name={file_name};base64,{project_content}'
            }
            response = self.client.put(url, data=json.dumps(data), content_type='application/json')
        service = Service.objects.get(name='project-1')
        file = service.project_file.file
        with file.open(mode='r') as f:
            content = f.read()
        self.assertTrue('projectname="project2"' in content.decode())

    def test_update_users(self):
        with open('tests/files/project1.qgs', 'rb') as f:
            service = Service.objects.create(
                name='project-1',
                active=False,
                project_file=File(f, name='project1.qgs')
            )
            for i in range(3):
                user = User.objects.create(
                    username=f'user{i}',
                    email=f'user{i}@mail.com'
                )
                ServiceUserPermission.objects.create(
                    service=service,
                    user=user,
                    can_view=True,
                    can_write=True
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
                            'username': 'user2',
                            'email': 'user2@mail.net'
                        },
                        'can_view': False,
                        'can_write': False
                    },
                    {
                        'user': {
                            'username': 'user3',
                            'email': 'user3@mail.net'
                        },
                        'can_view': False,
                        'can_write': False
                    }
                ],
                'group_permissions': [],
                'project_file': f'data:text/xml;charset=utf8-8;name={file_name};base64,{project_content}'
            }
            response = self.client.put(url, data=json.dumps(data), content_type='application/json')
        result = response.json()
        self.assertEqual(len(result['user_permissions']), 2)
        users = {}
        for permission in result['user_permissions']:
            users[permission['user']['username']] = permission

        self.assertTrue(users['user2']['user']['email'], 'user2@mail.net')
        self.assertTrue(users['user3']['user']['email'], 'user3@mail.net')

        self.assertFalse(users['user2']['can_view'])
        self.assertFalse(users['user2']['can_write'])
        self.assertFalse(users['user3']['can_view'])
        self.assertFalse(users['user3']['can_write'])

    def test_update_groups(self):
        with open('tests/files/project1.qgs', 'rb') as f:
            service = Service.objects.create(
                name='project-1',
                active=False,
                project_file=File(f, name='project1.qgs')
            )
            for i in range(3):
                group = Group.objects.create(
                    name=f'group{i}'
                )
                ServiceGroupPermission.objects.create(
                    service=service,
                    group=group,
                    can_view=True,
                    can_write=True
                )

        self.login_superuser()
        url = reverse('qgisserver_service-list')
        project_file_path = 'tests/files/project2.qgs'
        file_name = Path(project_file_path).name
        with open(project_file_path, 'rb') as project_file:
            project_content = base64.b64encode(project_file.read()).decode('utf-8')
            data = {
                'name': 'project-1',
                'user_permissions': [],
                'group_permissions': [
                    {
                        'group': {
                            'name': 'group2'
                        },
                        'can_view': False,
                        'can_write': False
                    },
                    {
                        'group': {
                            'name': 'group3'
                        },
                        'can_view': False,
                        'can_write': False,
                    }
                ],
                'project_file': f'data:text/xml;charset=utf8-8;name={file_name};base64,{project_content}'
            }
            response = self.client.put(url, data=json.dumps(data), content_type='application/json')
        result = response.json()

        self.assertEqual(len(result['group_permissions']), 2)
        groups = {}
        for permission in result['group_permissions']:
            groups[permission['group']['name']] = permission

        self.assertFalse(groups['group2']['can_view'])
        self.assertFalse(groups['group3']['can_view'])
        self.assertFalse(groups['group2']['can_write'])
        self.assertFalse(groups['group3']['can_write'])
