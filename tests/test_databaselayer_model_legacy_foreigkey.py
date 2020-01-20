from django.conf import settings
from django.test import TransactionTestCase

from giscube.models import DBConnection
from layerserver.model_legacy import get_fields
from tests.common import BaseTest


class DataBaseLayerModelLegacyForeigkeyCase(BaseTest, TransactionTestCase):
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
        self.conn = conn

    def tearDown(self):
        super().tearDown()

        cursor = self.conn.get_connection().cursor()
        sql = 'DROP TABLE IF EXISTS address'
        cursor.execute(sql)
        sql = 'DROP TABLE IF EXISTS street'
        cursor.execute(sql)

    def test_foreig_key_field(self):
        connection = self.conn.get_connection()
        sql = """
            CREATE TABLE street
            (
              id serial NOT NULL,
              code character varying(20),
              name character varying(255),
              geometry geometry(LineString,4326),
              CONSTRAINT street_id_pkey PRIMARY KEY (id),
              CONSTRAINT street_code_unique UNIQUE (code)
            );
        """
        cursor = connection.cursor()
        cursor.execute(sql)

        sql = """
            CREATE TABLE address
            (
              id serial NOT NULL,
              street_code character varying(20),
              address character varying(255),
              geometry geometry(Point,4326),
              CONSTRAINT address_id_pkey PRIMARY KEY (id),
              FOREIGN KEY (street_code) REFERENCES street (code)
            );
        """
        cursor = connection.cursor()
        cursor.execute(sql)

        fields = get_fields(connection, 'address', 'id')

        self.assertEqual(fields['street_code']['field_type'], 'CharField')
