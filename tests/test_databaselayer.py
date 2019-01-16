from django.conf import settings

from tests.common import BaseTest

from giscube.models import DBConnection
from layerserver.models import DataBaseLayer


class DataBaseLayerAPITestCase(BaseTest):
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
        layer.name = 'tests_location'
        layer.table = 'tests_location'
        layer.pk_field = 'id'
        layer.geometry_field = 'geometry'
        layer.save()
        self.layer = layer

    def test_fields_changed(self):
        conn = self.layer.db_connection.get_connection()
        self.assertEqual(1, self.layer.fields.filter(name='address').count())
        cursor = conn.cursor()
        cursor.execute('ALTER TABLE tests_location RENAME COLUMN address'
                       ' TO new_address;')
        conn.commit()
        self.layer.save()
        self.layer.refresh_from_db()
        self.assertEqual(0, self.layer.fields.filter(name='address').count())
        self.assertEqual(
            1, self.layer.fields.filter(name='new_address').count())

        cursor.execute('ALTER TABLE tests_location ADD COLUMN status VARCHAR;')
        conn.commit()
        self.layer.save()
        self.layer.refresh_from_db()
        self.assertEqual(1, self.layer.fields.filter(name='status').count())

        # Restore column name to avoid problems with other tests
        cursor.execute('ALTER TABLE tests_location RENAME COLUMN new_address'
                       ' TO address;')
        conn.commit()
