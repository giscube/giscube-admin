from django.conf import settings
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import ModelFactory
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
        layer.name = 'tests_specie'
        layer.table = 'tests_specie'
        layer.pk_field = 'code'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

        self.species = []
        with ModelFactory(layer) as Specie:
            for i in range(0, 12):
                s = Specie()
                s.code = 'QI%s' % str(i).zfill(3)
                s.address = 'Quercus ilex %s' % i
                s.save()
                self.species.append(s)

    def test_bulk_ok(self):
        data = {
            'ADD': [
                {
                    'code': 'A101',
                    'name': 'Almend 101',
                },
                {
                    'code': 'A102',
                    'name': 'Almend 102',
                },
            ],
            'UPDATE': [
                {
                    'code': self.species[5].code,
                    'name': 'Quercus ilex 5 (Temp)',
                }
            ],
            'DELETE': [self.species[9].code, self.species[10].code]
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        with ModelFactory(self.layer) as SpecieModel:
            obj = SpecieModel.objects.get(code=data['ADD'][0]['code'])
            self.assertEqual(obj.name, data['ADD'][0]['name'])
            obj = SpecieModel.objects.get(code=data['ADD'][1]['code'])
            self.assertEqual(obj.name, data['ADD'][1]['name'])

            obj = SpecieModel.objects.get(code=self.species[5].code)
            self.assertEqual(obj.name, data['UPDATE'][0]['name'])

            self.assertEqual(0, SpecieModel.objects.filter(code__in=data['DELETE']).count())

    def test_bulk_blank_nok(self):
        field = self.layer.fields.filter(name='name').first()
        field.blank = False
        field.save()

        data = {
            'ADD': [
                {
                    'code': 'A101'
                }
            ],
            'UPDATE': [
                {
                    'code': self.species[1].code,
                    'name': None
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
        self.assertEqual(result['ADD']['0']['name'][0], 'This field is required.')

    def test_bulk_not_found(self):
        data = {
            'ADD': [],
            'UPDATE': [
                {
                    'code': 'XXXX',
                    'name': 'Almend'
                }
            ],
            'DELETE': []
        }
        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)
