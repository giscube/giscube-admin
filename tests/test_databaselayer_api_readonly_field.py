from django.conf import settings
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer
from tests.common import BaseTest


class DataBaseLayerAPIReadonlyFieldTestCase(BaseTest):
    def setUp(self):
        super(self.__class__, self).setUp()
        conn = DBConnection()
        conn.alias = 'test_connection'
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

    def create_model(self, readonly_fields=None):
        readonly_fields = readonly_fields or ['address']
        self.layer.fields.filter(name__in=readonly_fields).update(readonly=True)

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

    def test_content_readonly(self):
        self.create_model()

        url = reverse('content-list', kwargs={'name': self.layer.name})
        data = {
            'code': 'A001',
            'address': 'Test',
            'geometry': 'POINT(0 0)'
        }
        response = self.client.post(url, data, format='json')
        res = response.json()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(res['properties']['address'], None)
        location = self.Location.objects.filter(code='A001').first()
        location.address = 'Test'
        location.save()
        location.refresh_from_db()
        self.assertEqual(location.address, 'Test')

        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': res['id']})
        data = {
            'address': 'Test Update'
        }
        response = self.client.patch(url, data, format='json')
        res = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(res['properties']['address'], 'Test')

    def test_bulk(self):
        self.create_model()

        data = {
            'ADD': [
                {
                    'code': 'A101',
                    'address': 'C/ Jaume 100, Girona',
                    'geometry': 'POINT (0 10)'
                },
                {
                    'code': 'A102',
                    'geometry': 'POINT (0 10)'
                }
            ],
            'UPDATE': [
                {
                    'id': self.locations[2].id,
                    'geometry': 'POINT (0 10)'
                }
            ],
            'DELETE': []
        }
        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        obj = self.Location.objects.get(code=data['ADD'][0]['code'])

        self.assertEqual(obj.address, None)

        obj = self.Location.objects.get(code=self.locations[2].code)
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
