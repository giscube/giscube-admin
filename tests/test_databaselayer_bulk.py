from django.conf import settings
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import ModelFactory, create_dblayer_model
from layerserver.models import DataBaseLayer
from tests.common import BaseTest


class DataBaseLayerBulkAPITestCase(BaseTest):
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
        layer.pk_field = 'code'
        layer.geom_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

        self.locations = []
        with ModelFactory(layer) as Location:
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
                    'code': self.locations[2].code,
                    'geometry': 'POINT (0 10)'
                },
                {
                    'code': self.locations[5].code,
                    'address': 'C/ Cor de Maria 5, Girona',
                    'geometry': 'POINT (11 10)'
                },
                {
                    'code': self.locations[1].code,
                    'address': 'C/ Cor de Maria 1, Girona'
                }
            ],
            'DELETE': [self.locations[9].code, self.locations[10].code]
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        Location = create_dblayer_model(self.layer)
        obj = Location.objects.get(code=data['ADD'][0]['code'])
        self.assertEqual(obj.geometry.wkt, data['ADD'][0]['geometry'])
        self.assertEqual(obj.address, data['ADD'][0]['address'])
        obj = Location.objects.get(code=data['ADD'][1]['code'])
        self.assertEqual(obj.geometry.wkt, data['ADD'][1]['geometry'])
        self.assertEqual(obj.address, data['ADD'][1]['address'])

        obj = Location.objects.get(code=self.locations[2].code)
        self.assertEqual(obj.geometry.wkt, data['UPDATE'][0]['geometry'])

        obj = Location.objects.get(code=self.locations[5].code)
        self.assertEqual(obj.address, data['UPDATE'][1]['address'])
        self.assertEqual(obj.geometry.wkt, data['UPDATE'][1]['geometry'])

        obj = Location.objects.get(code=self.locations[1].code)
        self.assertEqual(obj.address, data['UPDATE'][2]['address'])

        self.assertEqual(
            0, Location.objects.filter(code__in=data['DELETE']).count())

    def test_bulk_blank_nok(self):
        field = self.layer.fields.filter(name='address').first()
        field.blank = False
        field.save()

        data = {
            'ADD': [
                {
                    'code': 'A101',
                    'geometry': 'POINT (0 10)'
                }
            ],
            'UPDATE': [
                {
                    'code': self.locations[1].code,
                    'address': None
                }
            ],
            'DELETE': []
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertTrue('ADD' in result)
        self.assertEqual(len(result['ADD']), 1)
        self.assertEqual(result['ADD']['0']['address'][0], 'This field is required.')

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
                    'id': self.locations[2].code,
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [0, 10]
                    },
                    'properties': {}
                },
                {
                    'type': 'Feature',
                    'id': self.locations[5].code,
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
                    'id': self.locations[1].code,
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [11, 10]
                    },
                    'properties': {
                        'address': 'C/ Cor de Maria 1, Girona'
                    }
                }
            ],
            'DELETE': [self.locations[9].code, self.locations[10].code]
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        Location = create_dblayer_model(self.layer)
        obj = Location.objects.get(code=data['ADD'][0]['properties']['code'])
        self.assertEqual(list(obj.geometry.coords), data['ADD'][0]['geometry']['coordinates'])
        self.assertEqual(obj.address, data['ADD'][0]['properties']['address'])

        obj = Location.objects.get(code=data['ADD'][1]['properties']['code'])
        self.assertEqual(list(obj.geometry.coords), data['ADD'][1]['geometry']['coordinates'])
        self.assertEqual(obj.address, data['ADD'][1]['properties']['address'])

        obj = Location.objects.get(code=self.locations[2].code)
        self.assertEqual(list(obj.geometry.coords), data['UPDATE'][0]['geometry']['coordinates'])

        obj = Location.objects.get(code=self.locations[5].code)
        self.assertEqual(list(obj.geometry.coords), data['UPDATE'][1]['geometry']['coordinates'])
        self.assertEqual(obj.address, data['UPDATE'][1]['properties']['address'])

        obj = Location.objects.get(code=self.locations[1].code)
        self.assertEqual(list(obj.geometry.coords), data['UPDATE'][2]['geometry']['coordinates'])
        self.assertEqual(obj.address, data['UPDATE'][2]['properties']['address'])

        self.assertEqual(
            0, Location.objects.filter(code__in=data['DELETE']).count())

    def test_bulk_not_found(self):
        data = {
            'ADD': [],
            'UPDATE': [
                {
                    'code': 'XXXX',
                    'geometry': 'POINT (0 10)'
                },
                {
                    'code': self.locations[5].code,
                    'address': 'C/ Cor de Maria 5, Girona',
                    'geometry': 'POINT (11 10)'
                },
                {
                    'code': self.locations[1].code,
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
                    'code': self.locations[5].code,
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

    def test_bulk_update_without_geometry(self):
        old_geom = list(self.locations[5].geometry.coords)
        data = {
            'ADD': [],
            'UPDATE': [
                {
                    'code': self.locations[5].code,
                    'address': 'C/ Martí 5, Girona'
                }
            ],
            'DELETE': []
        }
        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        Location = create_dblayer_model(self.layer)
        obj = Location.objects.get(code=self.locations[5].code)
        self.assertEqual(old_geom, list(obj.geometry.coords))
        self.assertEqual(obj.address, 'C/ Martí 5, Girona')

    def test_bulk_update_without_geometry_geojson(self):
        old_geom = list(self.locations[5].geometry.coords)
        data = {
            'ADD': [],
            'UPDATE': [
                {
                    'type': 'Feature',
                    'id': self.locations[5].code,
                    'properties': {
                        'address': 'C/ Manel 5, Girona'
                    }
                }
            ],
            'DELETE': []
        }
        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        Location = create_dblayer_model(self.layer)
        obj = Location.objects.get(code=self.locations[5].code)
        self.assertEqual(old_geom, list(obj.geometry.coords))
        self.assertEqual(obj.address, 'C/ Manel 5, Girona')
