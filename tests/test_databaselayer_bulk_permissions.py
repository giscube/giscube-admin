from django.conf import settings
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import ModelFactory
from layerserver.models import DataBaseLayer
from tests.common import BaseTest


class DataBaseLayerBulkPermissionsTestCase(BaseTest):
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
        layer.anonymous_add = False
        layer.anonymous_update = False
        layer.anonymous_delete = False

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

    def send_data(self, filter=None):
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
        if filter:
            for k in list(data.keys()):
                if k not in filter:
                    del data[k]

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        return response.status_code

    def test_anonymous_permission_denied(self):
        status_code = self.send_data()
        self.assertEqual(status_code, 401)

    def test_anonymous_permission_denied_add(self):
        self.layer.anonymous_add = True
        self.layer.anonymous_update = False
        self.layer.anonymous_delete = False
        self.layer.save()
        status_code = self.send_data()
        self.assertEqual(status_code, 401)

    def test_anonymous_permission_denied_add_update(self):
        self.layer.anonymous_add = True
        self.layer.anonymous_update = False
        self.layer.anonymous_delete = False
        self.layer.save()
        status_code = self.send_data()
        self.assertEqual(status_code, 401)

    def test_anonymous_permission_denied_add_update_delete(self):
        self.layer.anonymous_add = True
        self.layer.anonymous_update = True
        self.layer.anonymous_delete = True
        self.layer.save()
        status_code = self.send_data()
        self.assertEqual(status_code, 200)

    def test_anonymous_permission_add(self):
        self.layer.anonymous_add = True
        self.layer.save()
        status_code = self.send_data('ADD')
        self.assertEqual(status_code, 200)

    def test_anonymous_permission_update(self):
        self.layer.anonymous_update = True
        self.layer.save()
        status_code = self.send_data('UPDATE')
        self.assertEqual(status_code, 200)

    def test_anonymous_permission_delete(self):
        self.layer.anonymous_delete = True
        self.layer.save()
        status_code = self.send_data('DELETE')
        self.assertEqual(status_code, 200)

    def test_anonymous_permission_add_fail(self):
        status_code = self.send_data('ADD')
        self.assertEqual(status_code, 401)

    def test_anonymous_permission_update_fail(self):
        status_code = self.send_data('UPDATE')
        self.assertEqual(status_code, 401)

    def test_anonymous_permission_delete_fail(self):
        status_code = self.send_data('DELETE')
        self.assertEqual(status_code, 401)
