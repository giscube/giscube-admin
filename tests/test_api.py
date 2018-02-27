from django.contrib.auth import get_user_model
from django.urls import reverse

from tests.common import BaseTest


UserModel = get_user_model()


class APITestCase(BaseTest):
    def setUp(self):
        super(self.__class__, self).setUp()

    def test_api_qgisserver_project_list_unathenticated(self):
        url = reverse('qgisserver_project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_api_qgisserver_project_list(self):
        self.login_test_user()
        url = reverse('qgisserver_project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
