from django.conf import settings
from django.test import TransactionTestCase

from giscube.models import DBConnection
from layerserver.admin_forms import DataBaseLayerAddForm
from layerserver.models import DataBaseLayer
from layerserver.model_legacy import create_dblayer_model
from tests.common import BaseTest


class DataBaseLayerPrimaryKeyCase(BaseTest, TransactionTestCase):
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
        cursor = self.conn.get_connection().cursor()
        sql = 'DROP TABLE IF EXISTS address_no_primary_key'
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)

    def test_add_form_autofield_add_primary_key(self):
        sql = """
            CREATE TABLE address_no_primary_key
            (
              id serial NOT NULL,
              address character varying(255),
              geometry geometry(Point,4326)
            );
        """
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)
        data = {
            'db_connection': self.conn.pk, 'slug': 'address_no_primary_key', 'name': 'address_no_primary_key',
            'table': 'public.address_no_primary_key', 'geom_field': 'geometry', 'srid': 4326, 'pk_field': None
            }
        form = DataBaseLayerAddForm(data=data)
        self.assertTrue(form.is_valid())

    def test_add_form_no_primary_key_no_autofield(self):
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
            'db_connection': self.conn.pk, 'slug': 'address_no_primary_key', 'name': 'address_no_primary_key',
            'table': 'public.address_no_primary_key', 'geom_field': 'geometry', 'srid': 4326, 'pk_field': None
            }
        form = DataBaseLayerAddForm(data=data)
        self.assertFalse(form.is_valid())

        data = {
            'db_connection': self.conn.pk, 'slug': 'address_no_primary_key', 'name': 'address_no_primary_key',
            'table': 'public.address_no_primary_key', 'geom_field': 'geometry', 'srid': 4326, 'pk_field': 'code'
            }
        form = DataBaseLayerAddForm(data=data)
        valid = form.is_valid()
        self.assertTrue(valid)

    def test_autofield_add_primary_key(self):
        """
        If there isn't a primary key it looks but a pk_field is defined sets primary_key=True to pk_field
        """
        sql = """
            CREATE TABLE address_no_primary_key
            (
              id serial NOT NULL,
              address character varying(255),
              geometry geometry(Point,4326)
            );
        """
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)

        layer = DataBaseLayer()
        layer.db_connection = self.conn
        layer.slug = 'address_no_primary_key'
        layer.name = 'address_no_primary_key'
        layer.table = 'address_no_primary_key'
        layer.pk_field = 'id'
        layer.geom_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()

        Model = create_dblayer_model(layer)

        primary_key = None
        for f in Model._meta.fields:
            if getattr(f, 'primary_key'):
                primary_key = f.name
                break
        self.assertEqual(primary_key, 'id')

    def test_code_add_primary_key(self):
        """
        If there isn't a primary key it looks but a pk_field is defined sets primary_key=True to pk_field
        """
        sql = """
            CREATE TABLE address_no_primary_key
            (
              code character varying(10),
              address character varying(255),
              geometry geometry(Point,4326)
            );
        """
        cursor = self.conn.get_connection().cursor()
        cursor.execute(sql)

        layer = DataBaseLayer()
        layer.db_connection = self.conn
        layer.slug = 'address_no_primary_key'
        layer.name = 'address_no_primary_key'
        layer.table = 'address_no_primary_key'
        layer.pk_field = 'code'
        layer.geom_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()

        Model = create_dblayer_model(layer)

        primary_key = None
        for f in Model._meta.fields:
            if getattr(f, 'primary_key'):
                primary_key = f.name
                break
        self.assertEqual(primary_key, 'code')
