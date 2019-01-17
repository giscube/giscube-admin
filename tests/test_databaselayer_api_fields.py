from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from tests.common import BaseTest

from giscube.models import DBConnection
from layerserver.models import DataBaseLayer


UserModel = get_user_model()


class DataBaseLayerAPIFieldsTestCase(BaseTest):
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
        layer.slug = 'tests_testfield'
        layer.name = 'tests_testfield'
        layer.table = 'tests_testfield'
        layer.pk_field = 'id'
        layer.geometry_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

    def test_layer_list_authenticated_anonymous_permission(self):
        url = reverse('layer-detail', kwargs={'slug': self.layer.slug})
        response = self.client.get(url)
        result = response.json()
        fields = {}
        for field in result['fields']:
            fields[field['name']] = field

        self.assertEqual(fields['id']['type'], 'number')
        self.assertEqual(fields['code']['type'], 'string')
        self.assertEqual(fields['name']['type'], 'string')
        self.assertEqual(fields['price']['type'], 'number')
        self.assertEqual(fields['x']['type'], 'number')
        self.assertEqual(fields['geometry']['type'], 'geometry')

        self.assertEqual(fields['id']['null'], False)
        self.assertEqual(fields['code']['null'], False)
        self.assertEqual(fields['name']['null'], True)
        self.assertEqual(fields['price']['null'], True)
        self.assertEqual(fields['x']['null'], True)
        self.assertEqual(fields['geometry']['null'], False)

        self.assertEqual(fields['id']['size'], None)
        self.assertEqual(fields['code']['size'], 10)
        self.assertEqual(fields['name']['size'], 50)
        self.assertEqual(fields['price']['size'], 8)
        self.assertEqual(fields['x']['size'], None)
        self.assertEqual(fields['geometry']['size'], None)

        self.assertEqual(fields['id']['decimals'], None)
        self.assertEqual(fields['code']['decimals'], None)
        self.assertEqual(fields['name']['decimals'], None)
        self.assertEqual(fields['price']['decimals'], 2)
        self.assertEqual(fields['x']['decimals'], None)
        self.assertEqual(fields['geometry']['decimals'], None)

    def test_geom_field_type(self):
        url = reverse('layer-detail', kwargs={'slug': self.layer.slug})
        response = self.client.get(url)
        result = response.json()
        self.assertEqual(result['geom_type'], 'POINT')
