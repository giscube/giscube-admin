from unittest import mock

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from giscube.models import DBConnection, GiscubeTransaction
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer
from tests.common import BaseTest


class DataBaseLayerBulkHashAPITestCase(BaseTest):
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
        layer.name = 'tests_location_25831'
        layer.table = 'tests_location_25831'
        layer.srid = 25831
        layer.pk_field = 'code'
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

        location = Location()
        location.code = 'C001'
        location.address = 'C/ Major 1, Salt'
        location.geometry = 'POINT(482984.669856201 4647181.21886241)'
        location.save()
        self.locations.append(location)

    def test_bulk_hash(self):
        data = {
            'ADD': [
                {
                    'code': 'C003',
                    'address': 'C/ Major 3, Salt',
                    'geometry': 'POINT (2.79450 41.97642)'
                }
            ],
            'UPDATE': [],
            'DELETE': [],
            '_META': {'time': timezone.now().isoformat()}
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        hash = response.request['HTTP_X_BULK_HASH']
        self.assertTrue(GiscubeTransaction.objects.filter(hash=hash).exists())

        response1 = response

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response1.json(), response.json())
        self.assertEqual(GiscubeTransaction.objects.all().count(), 1)

    @mock.patch('layerserver.api.DBLayerContentBulkViewSet.post')
    def test_bulk_hash_post_error(self, fake_post):
        fake_post.side_effect = Exception('Test')
        data = {
            'ADD': [
                {
                    'code': 'C003',
                    'address': 'C/ Major 3, Salt',
                    'geometry': 'POINT (2.79450 41.97642)'
                }
            ],
            'UPDATE': [],
            'DELETE': [],
            '_META': {'time': timezone.now().isoformat()}
        }
        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        try:
            self.client.post(url, data)
        except Exception:
            pass

        try:
            self.client.post(url, data)
        except Exception:
            pass

        _, hash = self.client.bulk_hash(data)
        filter = {'hash': hash, 'response_status_code': 500}
        transactions = GiscubeTransaction.objects.filter(**filter)
        self.assertEqual(transactions.count(), 2)
        first = transactions.first()
        last = transactions.last()
        self.assertEqual(first.hash, first.hash)
        self.assertEqual(transactions.first().error, 'Test')
