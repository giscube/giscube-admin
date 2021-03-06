from django.conf import settings
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer
from tests.common import BaseTest


class DataBaseLayerBulkIDAPITestCase(BaseTest):
    """
    Use normal id as pk_field
    """

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
        layer.name = 'tests_location'
        layer.table = 'tests_location'
        layer.pk_field = 'id'
        layer.geom_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

        self.locations = []
        Location = create_dblayer_model(layer)
        self.Location = Location
        for i in range(0, 12):
            location = Location()
            location.code = 'C%s' % str(i).zfill(3)
            location.address = 'C/ Jaume %s, Girona' % i
            location.geometry = 'POINT(0 %s)' % i
            location.save()
            self.locations.append(location)

    def test_bulk_ok(self):
        data = {
            'ADD': [
                {
                    'code': 'A101',
                    'address': 'C/ Jaume 100, Girona',
                    'geometry': 'POINT (0 10)'
                },
                {
                    'code': 'A102',
                    'address': 'C/ Jaume 100, Girona',
                    'geometry': 'POINT (11 10)'
                },
            ],
            'UPDATE': [
                {
                    'id': self.locations[2].id,
                    'geometry': 'POINT (0 10)'
                },
                {
                    'id': self.locations[5].id,
                    'address': 'C/ Cor de Maria 5, Girona',
                    'geometry': 'POINT (11 10)'
                },
                {
                    'id': self.locations[1].id,
                    'address': 'C/ Cor de Maria 1, Girona'
                }
            ],
            'DELETE': [self.locations[9].id, self.locations[10].id]
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        obj = self.Location.objects.get(code=data['ADD'][0]['code'])
        self.assertEqual(obj.geometry.wkt, data['ADD'][0]['geometry'])
        self.assertEqual(obj.address, data['ADD'][0]['address'])
        obj = self.Location.objects.get(code=data['ADD'][1]['code'])
        self.assertEqual(obj.geometry.wkt, data['ADD'][1]['geometry'])
        self.assertEqual(obj.address, data['ADD'][1]['address'])

        obj = self.Location.objects.get(id=self.locations[2].id)
        self.assertEqual(obj.geometry.wkt, data['UPDATE'][0]['geometry'])

        obj = self.Location.objects.get(id=self.locations[5].id)
        self.assertEqual(obj.address, data['UPDATE'][1]['address'])
        self.assertEqual(obj.geometry.wkt, data['UPDATE'][1]['geometry'])

        obj = self.Location.objects.get(id=self.locations[1].id)
        self.assertEqual(obj.address, data['UPDATE'][2]['address'])

        self.assertEqual(
            0, self.Location.objects.filter(code__in=data['DELETE']).count())

    def test_bulk_ok_geojson(self):
        data = {
            'ADD': [
                {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [0.0, 10.0]
                    },
                    'properties': {
                        'code': 'A101',
                        'address': 'C/ Jaume 100, Girona'
                    }
                },
                {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [11.0, 10.0]
                    },
                    'properties': {
                        'code': 'A102',
                        'address': 'C/ Jaume 100, Girona'
                    }
                }
            ],
            'UPDATE': [
                {
                    'type': 'Feature',
                    'id': self.locations[2].id,
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [0, 10]
                    },
                    'properties': {}
                },
                {
                    'type': 'Feature',
                    'id': self.locations[5].id,
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [11, 10]
                    },
                    'properties': {
                        'address': 'C/ Cor de Maria 5, Girona'
                    }
                },
                {
                    'type': 'Feature',
                    'id': self.locations[1].id,
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [11, 10]
                    },
                    'properties': {
                        'address': 'C/ Cor de Maria 1, Girona'
                    }
                }
            ],
            'DELETE': [self.locations[9].id, self.locations[10].id]
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        obj = self.Location.objects.get(code=data['ADD'][0]['properties']['code'])
        self.assertEqual(list(obj.geometry.coords), data['ADD'][0]['geometry']['coordinates'])
        self.assertEqual(obj.address, data['ADD'][0]['properties']['address'])

        obj = self.Location.objects.get(code=data['ADD'][1]['properties']['code'])
        self.assertEqual(list(obj.geometry.coords), data['ADD'][1]['geometry']['coordinates'])
        self.assertEqual(obj.address, data['ADD'][1]['properties']['address'])

        obj = self.Location.objects.get(id=self.locations[2].id)
        self.assertEqual(list(obj.geometry.coords), data['UPDATE'][0]['geometry']['coordinates'])

        obj = self.Location.objects.get(id=self.locations[5].id)
        self.assertEqual(list(obj.geometry.coords), data['UPDATE'][1]['geometry']['coordinates'])
        self.assertEqual(obj.address, data['UPDATE'][1]['properties']['address'])

        obj = self.Location.objects.get(id=self.locations[1].id)
        self.assertEqual(list(obj.geometry.coords), data['UPDATE'][2]['geometry']['coordinates'])
        self.assertEqual(obj.address, data['UPDATE'][2]['properties']['address'])

        self.assertEqual(
            0, self.Location.objects.filter(id__in=data['DELETE']).count())

    def test_bulk_not_found(self):
        data = {
            'ADD': [],
            'UPDATE': [
                {
                    'id': 100001,
                    'geometry': 'POINT (0 10)'
                },
                {
                    'id': self.locations[5].id,
                    'address': 'C/ Cor de Maria 5, Girona',
                    'geometry': 'POINT (11 10)'
                },
                {
                    'id': self.locations[1].id,
                    'address': 'C/ Cor de Maria 1, Girona'
                }
            ],
            'DELETE': []
        }
        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_bulk_geometry_null(self):
        data = {
            'ADD': [],
            'UPDATE': [
                {
                    'id': self.locations[5].id,
                    'address': 'C/ Cor de Maria 5, Girona',
                    'geometry': None
                }
            ],
            'DELETE': []
        }
        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertTrue('geometry' in result['UPDATE']['0'])
