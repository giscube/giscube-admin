from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from rest_framework.test import APIClient
from tests.common import BaseTest

from giscube.models import DBConnection
from layerserver.models import DataBaseLayer


class AdminDataBaseLayerAPITestCase(BaseTest):
    def setUp(self):
        super(self.__class__, self).setUp()
        conn = DBConnection()
        conn.alias = 'test'
        conn.engine = settings.DATABASES['default']['ENGINE']
        conn.name = settings.DATABASES['default']['NAME']
        conn.user = settings.DATABASES['default']['USER']
        conn.password = settings.DATABASES['default']['PASSWORD']
        conn.host = settings.DATABASES['default']['HOST']
        conn.port = settings.DATABASES['default']['PORT']
        conn.save()

        layer = DataBaseLayer()
        layer.db_connection = conn
        layer.name = 'tests_location'
        layer.slug = 'tests-location'
        layer.table = 'tests_location'
        layer.pk_field = 'id'
        layer.geom_field = 'geometry'
        layer.save()
        self.layer = layer

    def test_layer_content_unauthenticated(self):
        client = APIClient()
        url = reverse('admin-api-layer-content-list', args=(self.layer.slug,))
        response = client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_layer_content_authenticated_normal_user(self):
        client = APIClient()
        client.login(username='dev_user', password='123456')
        url = reverse('admin-api-layer-content-list', args=(self.layer.slug,))
        response = client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_layer_content_authenticated_staff_no_permission(self):
        client = APIClient()
        client.login(username='test_user', password='123456')
        url = reverse('admin-api-layer-content-list', args=(self.layer.slug,))
        response = client.get(url)
        self.assertEqual(response.status_code, 403)
        client.logout()

    def test_layer_content_authenticated_staff(self):
        client = APIClient()
        client.login(username='test_user', password='123456')
        content_type = ContentType.objects.get_for_model(DataBaseLayer)
        permission = Permission.objects.get(content_type=content_type, codename='view_databaselayer')
        self.test_user.user_permissions.add(permission)
        url = reverse('admin-api-layer-content-list', args=(self.layer.slug,))
        response = client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_layer_content_authenticated_superuser(self):
        client = APIClient()
        client.login(username='superuser', password='123456')
        url = reverse('admin-api-layer-content-list', args=(self.layer.slug,))
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
