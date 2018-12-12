from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from tests.common import BaseTest

from giscube.models import DBConnection
from layerserver.models import DataBaseLayer, DBLayerUser, DBLayerGroup


UserModel = get_user_model()


class DataBaseLayerAPITestCase(BaseTest):
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
        layer.table = 'tests_location'
        layer.pk_field = 'id'
        layer.geometry_field = 'geometry'
        layer.save()
        self.layer = layer

    def test_layer_list_unathenticated(self):
        url = reverse('layer-list')
        response = self.client.get(url)
        result = response.json()
        self.assertEqual(len(result), 0)

    def test_layer_list_authenticated_anonymous_permission(self):
        self.layer.anonymous_view = True
        self.layer.save()

        url = reverse('layer-list')
        response = self.client.get(url)
        result = response.json()
        self.assertEqual(len(result), 1)

    def test_layer_list_authenticated_user_permission_nothing_enabled(self):
        self.login_test_user()
        url = reverse('layer-list')

        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = False
        permission.can_add = False
        permission.can_update = False
        permission.can_delete = False
        permission.save()
        response = self.client.get(url)
        result = response.json()
        self.assertEqual(len(result), 0)

    def test_layer_list_authenticated_user_permission(self):
        self.login_test_user()
        url = reverse('layer-list')

        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = True
        permission.can_edit = False
        permission.can_delete = False
        permission.save()

        response = self.client.get(url)
        result = response.json()
        self.assertEqual(len(result), 1)

    def test_layer_list_authenticated_group_permission(self):
        self.login_test_user()
        url = reverse('layer-list')
        response = self.client.get(url)
        result = response.json()
        self.assertEqual(len(result), 0)

        g = Group()
        g.name = 'test'
        g.save()
        g.user_set.add(self.test_user)

        permission = DBLayerGroup()
        permission.can_view = True
        permission.can_edit = False
        permission.can_update = False
        permission.can_delete = False
        permission.layer = self.layer
        permission.group = g
        permission.save()

        response = self.client.get(url)
        result = response.json()
        self.assertEqual(len(result), 1)
