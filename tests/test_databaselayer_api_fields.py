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
        layer.name = 'tests-testfield'
        layer.table = 'tests_testfield'
        layer.pk_field = 'id'
        layer.geom_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

    def test_layer_fields(self):
        url = reverse('layer-detail', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        result = response.json()
        fields = {}
        for field in result['fields']:
            fields[field['name']] = field

        self.assertEqual(fields['id']['widget'], 'number')
        self.assertEqual(fields['code']['widget'], 'string')
        self.assertEqual(fields['name']['widget'], 'string')
        self.assertEqual(fields['price']['widget'], 'number')
        self.assertEqual(fields['enabled']['widget'], 'boolean')
        self.assertEqual(fields['accepted']['widget'], 'boolean')
        self.assertEqual(fields['x']['widget'], 'number')
        self.assertEqual(fields['geometry']['widget'], 'geometry')

        self.assertEqual(fields['id']['null'], False)
        self.assertEqual(fields['code']['null'], False)
        self.assertEqual(fields['name']['null'], True)
        self.assertEqual(fields['enabled']['null'], False)
        self.assertEqual(fields['accepted']['null'], True)
        self.assertEqual(fields['price']['null'], True)
        self.assertEqual(fields['x']['null'], True)
        self.assertEqual(fields['geometry']['null'], False)

        self.assertEqual(fields['id']['blank'], False)
        self.assertEqual(fields['code']['blank'], False)
        self.assertEqual(fields['name']['blank'], True)
        self.assertEqual(fields['enabled']['blank'], False)
        self.assertEqual(fields['accepted']['blank'], True)
        self.assertEqual(fields['price']['blank'], True)
        self.assertEqual(fields['x']['blank'], True)
        self.assertEqual(fields['geometry']['blank'], False)

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
        url = reverse('layer-detail', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        result = response.json()
        self.assertEqual(result['geom_type'], 'POINT')
