from datetime import datetime

from django.conf import settings
from django.urls import reverse
from django.utils.timezone import get_current_timezone

from giscube.models import DBConnection
from layerserver.model_legacy import ModelFactory, create_dblayer_model
from layerserver.models import DataBaseLayer, DataBaseLayerField
from tests.common import BaseTest


class DataBaseLayerWidgetAutoFillTestCase(BaseTest):
    def setUp(self):
        super(self.__class__, self).setUp()
        conn = DBConnection()
        conn.alias = "test"
        conn.engine = settings.DATABASES['default']['ENGINE']
        conn.name = settings.DATABASES['default']['NAME']
        conn.user = settings.DATABASES['default']['USER']
        conn.password = settings.DATABASES['default']['PASSWORD']
        conn.host = settings.DATABASES['default']['HOST']
        conn.port = settings.DATABASES['default']['PORT']
        conn.save()

        layer = DataBaseLayer()
        layer.db_connection = conn
        layer.name = 'tests_locationauto'
        layer.table = 'tests_locationauto'
        layer.pk_field = 'code'
        layer.geom_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        layer.refresh_from_db()
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

    def test_bulk_creationuser(self):
        field = self.layer.fields.filter(name='creationuser').first()
        field.widget = DataBaseLayerField.WIDGET_CHOICES.creationuser
        field.readonly = True
        field.save()

        code = 'A101'

        self.login_test_user()
        data = {
            'ADD': [
                {
                    'code': code,
                    'address': 'C/ Jaume 100, Girona',
                    'geometry': 'POINT (0 10)'
                }
            ],
            'UPDATE': [],
            'DELETE': []
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        Location = create_dblayer_model(self.layer)
        obj = Location.objects.get(code=code)
        self.assertTrue(obj.creationuser, 'test_user')

        self.login_dev_user()
        data = {
            'ADD': [],
            'UPDATE': [
                {
                    'code': code,
                    'geometry': 'POINT (0 10)'
                },
            ],
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        obj = Location.objects.get(code=code)
        self.assertTrue(obj.creationuser, 'test_user')

    def test_bulk_modificationuser(self):
        field = self.layer.fields.filter(name='modificationuser').first()
        field.widget = DataBaseLayerField.WIDGET_CHOICES.modificationuser
        field.readonly = True
        field.save()

        code = 'A101'

        self.login_test_user()
        data = {
            'ADD': [
                {
                    'code': code,
                    'address': 'C/ Jaume 100, Girona',
                    'geometry': 'POINT (0 10)'
                }
            ],
            'UPDATE': [],
            'DELETE': []
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        Location = create_dblayer_model(self.layer)
        obj = Location.objects.get(code=code)
        self.assertIsNone(obj.modificationuser)

        self.login_dev_user()
        data = {
            'ADD': [],
            'UPDATE': [
                {
                    'code': code,
                    'geometry': 'POINT (0 10)'
                },
            ],
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        obj = Location.objects.get(code=code)
        self.assertTrue(obj.modificationuser, 'test_user')

    def test_bulk_creationdate_create(self):
        field = self.layer.fields.filter(name='creationdate').first()
        field.widget = DataBaseLayerField.WIDGET_CHOICES.creationdate
        field.readonly = True
        field.save()

        code = 'A101'
        today = datetime.now(tz=get_current_timezone())

        self.login_test_user()
        data = {
            'ADD': [
                {
                    'code': code,
                    'address': 'C/ Jaume 100, Girona',
                    'geometry': 'POINT (0 10)'
                }
            ],
            'UPDATE': [],
            'DELETE': []
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        Location = create_dblayer_model(self.layer)
        obj = Location.objects.get(code=code)
        self.assertIsNotNone(obj.creationdate)
        self.assertEqual(obj.creationdate, today.date())

    def test_bulk_modificationdate(self):
        field = self.layer.fields.filter(name='modificationdate').first()
        field.widget = DataBaseLayerField.WIDGET_CHOICES.modificationdate
        field.readonly = True
        field.save()

        code = 'A101'
        today = datetime.now(tz=get_current_timezone())

        self.login_test_user()
        data = {
            'ADD': [
                {
                    'code': code,
                    'address': 'C/ Jaume 100, Girona',
                    'geometry': 'POINT (0 10)'
                }
            ],
            'UPDATE': [],
            'DELETE': []
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        Location = create_dblayer_model(self.layer)
        obj = Location.objects.get(code=code)
        self.assertIsNone(obj.modificationdate)

        data = {
            'ADD': [],
            'UPDATE': [
                {
                    'code': code,
                    'geometry': 'POINT (0 10)'
                },
            ],
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        obj = Location.objects.get(code=code)
        self.assertEqual(obj.modificationdate, today.date())

    def test_bulk_datetime(self):
        field = self.layer.fields.filter(name='creationdatetime').first()
        field.widget = DataBaseLayerField.WIDGET_CHOICES.creationdatetime
        field.readonly = True
        field.save()

        field = self.layer.fields.filter(name='modificationdatetime').first()
        field.widget = DataBaseLayerField.WIDGET_CHOICES.modificationdatetime
        field.readonly = True
        field.save()

        code = 'A101'
        today = datetime.now(tz=get_current_timezone())

        self.login_test_user()
        data = {
            'ADD': [
                {
                    'code': code,
                    'address': 'C/ Jaume 100, Girona',
                    'geometry': 'POINT (0 10)'
                }
            ],
            'UPDATE': [],
            'DELETE': []
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        Location = create_dblayer_model(self.layer)
        obj = Location.objects.get(code=code)
        self.assertIsNotNone(obj.creationdatetime)
        self.assertTrue(obj.creationdatetime >= today)

        data = {
            'ADD': [],
            'UPDATE': [
                {
                    'code': code,
                    'geometry': 'POINT (0 10)'
                },
            ],
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        obj = Location.objects.get(code=code)
        self.assertIsNotNone(obj.modificationdatetime)
        self.assertTrue(obj.modificationdatetime >= today)
