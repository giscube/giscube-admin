from django.conf import settings
from django.test import TransactionTestCase

from giscube.models import DBConnection
from layerserver.admin_forms import DataBaseLayerAddForm
from tests.common import BaseTest


class DataBaseLayerGeomFieldSchemaCase(BaseTest, TransactionTestCase):
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
        sql = 'DROP TABLE IF EXISTS address_no_primary_key'
        cursor.execute(sql)
        sql = 'DROP TABLE IF EXISTS public.address_no_primary_key'
        cursor.execute(sql)
        sql = 'DROP TABLE IF EXISTS "%s".address_no_primary_key' % self.conn.user
        cursor.execute(sql)
        sql = 'DROP SCHEMA IF EXISTS "%s"' % self.conn.user
        cursor.execute(sql)

    def test_no_schema(self):
        sql = """
            CREATE TABLE address_no_primary_key
            (
              code character varying(255),
              address character varying(255),
              geometry geometry(Point,4326)
            );
        """
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)

        data = {
            'db_connection': self.conn.pk, 'name': 'address_no_primary_key',
            'table': 'address_no_primary_key', 'geom_field': 'geometry', 'srid': 4326, 'pk_field': 'code'
        }
        form = DataBaseLayerAddForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)

    def test_schema_public(self):
        self.conn.get_connection()
        sql = """
            CREATE TABLE public.address_no_primary_key
            (
              code character varying(255),
              address character varying(255),
              geometry geometry(Point,4326)
            );
        """
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)

        data = {
            'db_connection': self.conn.pk, 'name': 'address_no_primary_key',
            'table': 'address_no_primary_key', 'geom_field': 'geometry', 'srid': 4326, 'pk_field': 'code'
        }
        form = DataBaseLayerAddForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)

    def test_schema_user(self):
        sql = """
            CREATE SCHEMA "%s";
        """ % self.conn.user
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)

        sql = """
            CREATE TABLE "%s".address_no_primary_key
            (
              code character varying(255),
              address character varying(255),
              geometry geometry(Point,4326)
            );
        """ % self.conn.user
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)

        data = {
            'db_connection': self.conn.pk, 'name': 'address_no_primary_key',
            'table': 'address_no_primary_key', 'geom_field': 'geometry', 'srid': 4326, 'pk_field': 'code'
        }
        form = DataBaseLayerAddForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)

    def test_schema_user_public(self):
        sql = """
            CREATE SCHEMA "%s";
        """ % self.conn.user
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)

        sql = """
            CREATE TABLE "%s".address_no_primary_key
            (
              address_code character varying(255),
              address character varying(255)
            );
        """ % self.conn.user
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)

        sql = """
            CREATE TABLE public.address_no_primary_key
            (
              code character varying(255),
              address character varying(255),
              geometry geometry(Point,4326)
            );
        """
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)

        data = {
            'db_connection': self.conn.pk, 'name': 'address_no_primary_key',
            'table': 'public.address_no_primary_key', 'geom_field': 'geometry', 'srid': 4326, 'pk_field': 'code'
        }
        form = DataBaseLayerAddForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)
