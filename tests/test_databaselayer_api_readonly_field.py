# -*- coding: utf-8 -*-


from django.conf import settings
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.models import DataBaseLayer
from tests.common import BaseTest

from layerserver.model_legacy import create_dblayer_model


class DataBaseLayerAPIReadonlyFieldTestCase(BaseTest):
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
        layer.slug = 'tests_location'
        layer.name = 'tests_location'
        layer.table = 'tests_location'
        layer.pk_field = 'id'
        layer.geometry_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

        self.layer.fields.filter(name='address').update(readonly=True)
        print(self.layer.fields.filter(name='address').first().__dict__)

        self.locations = []
        Location = create_dblayer_model(layer)
        self.Location = Location
        for i in range(0, 4):
            location = Location()
            location.code = 'C%s' % str(i).zfill(3)
            location.address = 'C/ Jaume %s, Girona' % i
            location.geometry = 'POINT(0 %s)' % i
            location.save()
            self.locations.append(location)

    def test_content_readonly(self):
        url = reverse('content-list', kwargs={'layer_slug': self.layer.slug})
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

        url = reverse('content-detail', kwargs={'layer_slug': self.layer.slug, 'pk': res['id']})
        data = {
            'address': 'Test Update'
        }
        response = self.client.patch(url, data, format='json')
        res = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(res['properties']['address'], 'Test')


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
        url = reverse('content-bulk', kwargs={'layer_slug': self.layer.slug})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 204)
        obj = self.Location.objects.get(code=data['ADD'][0]['code'])

        self.assertEqual(obj.address, None)

        obj = self.Location.objects.get(code=self.locations[2].code)
        self.assertEqual(obj.address, 'C/ Jaume 2, Girona')
