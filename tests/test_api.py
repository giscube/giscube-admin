from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

from tests.common import BaseTest


UserModel = get_user_model()


class APITestCase(BaseTest):
    def setUp(self):
        super(self.__class__, self).setUp()

    def add_permissions(self):
        codes = ['view_project', 'view_service']
        permissions = Permission.objects.filter(codename__in=codes, content_type__app_label='qgisserver')
        self.dev_user.user_permissions.add(*permissions)

    def test_api_qgisserver_project_list_unathenticated(self):
        url = reverse('qgisserver_project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_api_qgisserver_project_list(self):
        self.login_dev_user()
        url = reverse('qgisserver_project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.add_permissions()
        url = reverse('qgisserver_project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_api_qgisserver_service_list_unathenticated(self):
        url = reverse('qgisserver_service-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_api_qgisserver_service_list(self):
        self.login_dev_user()
        url = reverse('qgisserver_service-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.add_permissions()
        url = reverse('qgisserver_service-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
