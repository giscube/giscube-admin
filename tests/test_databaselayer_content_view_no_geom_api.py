from django.conf import settings
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer, DBLayerUser
from tests.common import BaseTest


class DataBaseLayerContentViewNoGeomAPITestCase(BaseTest):
    def setUp(self):
        super(self.__class__, self).setUp()
        conn = DBConnection()
        conn.alias = 'conn'
        conn.engine = settings.DATABASES['default']['ENGINE']
        conn.name = settings.DATABASES['default']['NAME']
        conn.user = settings.DATABASES['default']['USER']
        conn.password = settings.DATABASES['default']['PASSWORD']
        conn.host = settings.DATABASES['default']['HOST']
        conn.port = settings.DATABASES['default']['PORT']
        conn.save()

        layer = DataBaseLayer()
        layer.db_connection = conn
        layer.name = 'tests_specie'
        layer.table = 'tests_specie'
        layer.pk_field = 'id'
        layer.save()
        self.layer = layer

        Specie = create_dblayer_model(layer)
        specie = Specie()
        specie.code = 'quercusilex'
        specie.name = 'Quercus ilex'
        specie.save()
        self.specie = specie
        self.SpecienModel = Specie

        permission = DBLayerUser()
        permission.user = self.test_user
        permission.layer = self.layer
        permission.can_view = True
        permission.can_add = True
        permission.can_update = True
        permission.can_delete = True
        permission.save()

    def test_content_list(self):
        self.login_test_user()
        url = reverse('content-list', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data'][0]['name'], 'Quercus ilex')

    def test_content_add(self):
        self.login_test_user()
        url = reverse('content-list', kwargs={'name': self.layer.name})
        data = {
            'code': '01',
            'name': 'Test'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        result = response.json()
        self.assertEqual(result['code'], '01')
        self.assertEqual(result['name'], 'Test')

    def test_content_detail(self):
        self.login_test_user()
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.specie.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['code'], 'quercusilex')
        self.assertEqual(result['name'], 'Quercus ilex')

    def test_content_update(self):
        self.login_test_user()
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.specie.pk})
        data = {
            'name': 'Quercus ilex 2',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['name'], 'Quercus ilex 2')

    def test_content_delete(self):
        self.login_test_user()
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': self.specie.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
