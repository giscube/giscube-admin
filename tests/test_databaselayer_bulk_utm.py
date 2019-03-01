# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.urls import reverse
from django.test import TransactionTestCase

from giscube.models import DBConnection
from layerserver.models import DataBaseLayer
from tests.common import BaseTest

from layerserver.model_legacy import create_dblayer_model


class DataBaseLayerBulkUTMAPITestCase(BaseTest, TransactionTestCase):
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
        layer.slug = 'tests_location_25831'
        layer.name = 'tests_location_25831'
        layer.table = 'tests_location_25831'
        layer.srid = 25831
        layer.pk_field = 'code'
        layer.geometry_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

        self.locations = []
        Location = create_dblayer_model(layer)
        self.Location = Location

        location = Location()
        location.code = 'C001'
        location.address = 'C/ Major 1, Salt'
        location.geometry = 'POINT(482984.669856201 4647181.21886241)'
        location.save()
        self.locations.append(location)

    def test_bulk_4326(self):
        data = {
            'ADD': [
                {
                    'code': 'C003',
                    'address': 'C/ Major 3, Salt',
                    'geometry': 'POINT (2.79450 41.97642)'
                }
            ],
            'UPDATE': [
                {
                    'code': self.locations[0].code,
                    'geometry': 'POINT(2.79494 41.97648)'
                },
            ],
            'DELETE': []
        }

        url = reverse('content-bulk', kwargs={'layer_slug': self.layer.slug})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 204)

        obj = self.Location.objects.get(code=data['ADD'][0]['code'])
        self.assertAlmostEqual(obj.geometry.x, 482974.6931716673, places=6)
        self.assertAlmostEqual(obj.geometry.y, 4647178.590265266, places=6)

        obj = self.Location.objects.get(code=self.locations[0].code)
        self.assertAlmostEqual(obj.geometry.x, 483011.1623463448, places=6)
        self.assertAlmostEqual(obj.geometry.y, 4647185.164621412, places=6)

    def test_bulk_utm(self):
        data = {
            'ADD': [
                {
                    'code': 'C003',
                    'address': 'C/ Major 3, Salt',
                    'geometry': 'SRID=25831;POINT (482974.6931716673 4647178.590265266)'
                }
            ],
            'UPDATE': [
                {
                    'code': self.locations[0].code,
                    'geometry': 'SRID=25831;POINT(483011.1623463448 4647185.164621412)'
                },
            ],
            'DELETE': []
        }

        url = reverse('content-bulk', kwargs={'layer_slug': self.layer.slug})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 204)

        obj = self.Location.objects.get(code=data['ADD'][0]['code'])
        self.assertEqual(obj.geometry.wkt, 'POINT (482974.6931716673 4647178.590265266)')

        obj = self.Location.objects.get(code=self.locations[0].code)
        self.assertEqual(obj.geometry.wkt, 'POINT (483011.1623463448 4647185.164621412)')
