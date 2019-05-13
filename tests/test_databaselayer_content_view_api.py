from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer, DBLayerGroup, DBLayerUser
from tests.common import BaseTest


UserModel = get_user_model()


class DataBaseLayerContentViewAPITestCase(BaseTest):
    def setUp(self):
        super(self.__class__, self).setUp()
        conn = DBConnection()
        conn.alias = 'pepito'
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
        layer.geom_field = 'geometry'
        layer.save()
        self.layer = layer

        Location = create_dblayer_model(layer)
        location = Location()
        location.address = 'C/ Jaume 1, Girona'
        location.geometry = 'POINT(0 1)'
        location.save()
        self.location = location

        self.LocationModel = Location

    def test_content_list_unathenticated(self):
        url = reverse('content-list', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_content_list_authenticated_anonymous_permission(self):
        self.layer.anonymous_view = True
        self.layer.save()

        url = reverse('content-list', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_content_list_authenticated_user_permission_empty(self):
        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = False
        permission.can_add = True
        permission.can_update = True
        permission.can_delete = True
        permission.save()

        self.login_test_user()
        url = reverse('content-list', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_content_list_authenticated_user_permission_can_view(self):
        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = True
        permission.can_add = False
        permission.can_update = False
        permission.can_delete = False
        permission.save()

        self.login_test_user()
        url = reverse('content-list', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_content_list_authenticated_group_permission_can_view(self):
        g = Group()
        g.name = 'test'
        g.save()
        g.user_set.add(self.test_user)

        permission = DBLayerGroup()
        permission.can_view = True
        permission.can_edit = False
        permission.can_delete = False
        permission.can_update = False
        permission.layer = self.layer
        permission.group = g
        permission.save()

        self.login_test_user()
        url = reverse('content-list', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_content_add_unathenticated(self):
        url = reverse('content-list', kwargs={'name': self.layer.name})
        data = {
            'address': 'Test',
            'geometry': 'POINT(0,0)'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_content_add_authenticated_anonymous_permission(self):
        self.layer.anonymous_add = True
        self.layer.save()

        url = reverse('content-list', kwargs={'name': self.layer.name})
        data = {
            'code': '01',
            'address': 'Test',
            'geometry': 'POINT(0 0)'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_content_add_authenticated_user_permission_empty(self):
        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = True
        permission.can_add = False
        permission.can_update = True
        permission.can_delete = True
        permission.save()

        url = reverse('content-list', kwargs={'name': self.layer.name})
        data = {
            'code': '01',
            'address': 'Test',
            'geometry': 'POINT(0 0)'
        }
        self.login_test_user()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_content_add_authenticated_user_permission_can_add(self):
        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = True
        permission.can_add = True
        permission.can_update = False
        permission.can_delete = False
        permission.save()

        self.login_test_user()
        url = reverse('content-list', kwargs={'name': self.layer.name})
        data = {
            'code': '01',
            'address': 'Test',
            'geometry': 'POINT(0 0)'
        }
        self.login_test_user()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_content_add_authenticated_group_permission_can_add(self):
        g = Group()
        g.name = 'test'
        g.save()
        g.user_set.add(self.test_user)

        permission = DBLayerGroup()
        permission.can_view = True
        permission.can_edit = False
        permission.can_delete = False
        permission.can_update = False
        permission.layer = self.layer
        permission.group = g
        permission.save()

        self.login_test_user()
        url = reverse('content-list', kwargs={'name': self.layer.name})
        data = {
            'code': '01',
            'address': 'Test',
            'geometry': 'POINT(0 0)'
        }
        self.login_test_user()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_content_detail_unathenticated(self):
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_content_detail_authenticated_anonymous_permission(self):
        self.layer.anonymous_view = True
        self.layer.save()

        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_content_detail_authenticated_user_permission_empty(self):
        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = False
        permission.can_add = True
        permission.can_update = True
        permission.can_delete = True
        permission.save()

        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_content_detail_authenticated_user_permission_can_add(self):
        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = True
        permission.can_add = True
        permission.can_update = False
        permission.can_delete = False
        permission.save()

        self.login_test_user()
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_content_detail_authenticated_group_permission_can_add(self):
        g = Group()
        g.name = 'test'
        g.save()
        g.user_set.add(self.test_user)

        permission = DBLayerGroup()
        permission.can_view = True
        permission.can_edit = False
        permission.can_delete = False
        permission.can_update = False
        permission.layer = self.layer
        permission.group = g
        permission.save()

        self.login_test_user()
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_content_update_unathenticated(self):
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        data = {
            'address': 'Test',
            'geometry': 'POINT(0 0)'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_content_update_authenticated_anonymous_permission(self):
        self.layer.anonymous_view = True
        self.layer.anonymous_update = True
        self.layer.save()

        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        data = {
            'code': '01',
            'address': 'Test',
            'geometry': 'POINT(0 0)'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_content_update_authenticated_user_permission_empty(self):
        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = True
        permission.can_add = True
        permission.can_update = False
        permission.can_delete = True
        permission.save()

        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        data = {
            'code': '01',
            'address': 'Test',
            'geometry': 'POINT(0 0)'
        }
        self.login_test_user()
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_content_update_authenticated_user_permission_can_update(self):
        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = False
        permission.can_add = False
        permission.can_update = True
        permission.can_delete = False
        permission.save()

        self.login_test_user()
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        data = {
            'code': '01',
            'address': 'Test',
            'geometry': 'POINT(0 0)'
        }
        self.login_test_user()
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_content_add_authenticated_group_permission_can_update(self):
        g = Group()
        g.name = 'test'
        g.save()
        g.user_set.add(self.test_user)

        permission = DBLayerGroup()
        permission.can_view = False
        permission.can_edit = False
        permission.can_delete = False
        permission.can_update = True
        permission.layer = self.layer
        permission.group = g
        permission.save()

        self.login_test_user()
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        data = {
            'code': '01',
            'address': 'Test',
            'geometry': 'POINT(0 0)'
        }
        self.login_test_user()
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)

    def test_content_delete_unathenticated(self):
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    def test_content_delete_authenticated_anonymous_permission(self):
        self.layer.anonymous_delete = True
        self.layer.save()

        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_content_delete_authenticated_user_permission_empty(self):
        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = False
        permission.can_add = False
        permission.can_update = False
        permission.can_delete = True
        permission.save()

        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    def test_content_delete_authenticated_user_permission_can_delete(self):
        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = False
        permission.can_add = False
        permission.can_update = False
        permission.can_delete = True
        permission.save()

        self.login_test_user()
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_content_delete_authenticated_group_permission_can_delete(self):
        g = Group()
        g.name = 'test'
        g.save()
        g.user_set.add(self.test_user)

        permission = DBLayerGroup()
        permission.can_view = False
        permission.can_edit = False
        permission.can_delete = True
        permission.can_update = False
        permission.layer = self.layer
        permission.group = g
        permission.save()

        self.login_test_user()
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.location.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
