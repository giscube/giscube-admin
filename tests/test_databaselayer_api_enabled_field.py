from django.conf import settings
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer
from tests.common import BaseTest


class DataBaseLayerAPIEnabledFieldTestCase(BaseTest):
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
        layer.name = 'tests-location'
        layer.table = 'tests_locationnullgeometry'
        layer.pk_field = 'id'
        layer.geom_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

    def create_model(self, disabled_fields=None):
        disabled_fields = disabled_fields or ['address']
        self.layer.fields.filter(name__in=disabled_fields).update(enabled=False)

        self.locations = []
        Location = create_dblayer_model(self.layer)
        self.Location = Location
        for i in range(0, 4):
            location = Location()
            location.code = 'C%s' % str(i).zfill(3)
            location.address = 'C/ Jaume %s, Girona' % i
            location.geometry = 'POINT(0 %s)' % i
            location.save()
            self.locations.append(location)

    def test_no_address_serialized(self):
        self.create_model()
        url = reverse('content-list', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        feature = response.json()['features'][0]
        self.assertTrue('address' not in feature)

    def test_bulk(self):
        self.create_model()
        obj = self.Location.objects.get(pk=self.locations[2].id)
        self.assertEqual(obj.address, 'C/ Jaume 2, Girona')
        data = {
            'ADD': [
                {
                    'code': 'A901',
                    'address': 'Major 4, Girona',
                    'geometry': 'POINT (0 35)'
                }
            ],
            'UPDATE': [
                {
                    'id': self.locations[2].id,
                    'address': 'Major 4, Girona'
                }
            ],
            'DELETE': []
        }
        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        result = response.json()
        obj = self.Location.objects.get(pk=result['ADD'][0]['id'])
        self.assertEqual(obj.address, None)
        obj = self.Location.objects.get(pk=self.locations[2].id)
        self.assertEqual(obj.address, 'C/ Jaume 2, Girona')

    def test_bulk_geom(self):
        self.create_model(['geometry'])

        data = {
            'ADD': [
                {
                    'code': 'A101',
                    'geometry': 'POINT (0 25)'
                }
            ],
            'UPDATE': [
                {
                    'id': self.locations[2].id,
                    'geometry': 'POINT (0 25)'
                }
            ],
            'DELETE': []
        }
        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        result = response.json()
        self.assertEqual(response.status_code, 200)
        obj = self.Location.objects.get(pk=result['ADD'][0]['id'])
        self.assertEqual(obj.geometry, None)

        obj = self.Location.objects.get(pk=self.locations[2].id)
        self.assertEqual(obj.geometry.wkt, 'POINT (0 2)')
