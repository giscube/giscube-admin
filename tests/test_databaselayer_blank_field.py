from django.conf import settings

from giscube.models import DBConnection
from layerserver.model_legacy import ModelFactory
from layerserver.models import DataBaseLayer
from layerserver.serializers import create_dblayer_geom_serializer
from tests.common import BaseTest


class DataBaseLayerBlankFieldTestCase(BaseTest):
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
        layer.pk_field = 'code'
        layer.geom_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

    def test_blank(self):
        with ModelFactory(self.layer) as Location:
            self.assertEqual(Location._meta.get_field('address').blank, True)

            blanks = {}
            for field in self.layer.fields.all():
                blanks[field.name] = field.blank

            self.assertFalse(blanks['code'])
            self.assertTrue(blanks['address'])
            self.assertFalse(blanks['geometry'])

            field = self.layer.fields.filter(name='address').first()
            field.blank = False
            field.save()
            self.layer.refresh_from_db()
            blanks = {}
            for field in self.layer.fields.all():
                blanks[field.name] = field.blank

            self.assertFalse(blanks['code'])
            self.assertFalse(blanks['address'])
            self.assertFalse(blanks['geometry'])

        with ModelFactory(self.layer) as Location:
            self.assertEqual(Location._meta.get_field('address').blank, False)

            fields = []
            readonly_fields = []
            for field in self.layer.fields.filter(enabled=True):
                fields.append(field.name)
                if field.readonly is True:
                    readonly_fields.append(field.name)

            Serializer = create_dblayer_geom_serializer(Location, fields, self.layer.pk_field, readonly_fields)
            extra_kwargs = Serializer.Meta.extra_kwargs

            self.assertTrue(extra_kwargs['code']['required'])
            self.assertTrue(extra_kwargs['address']['required'])
            self.assertTrue(extra_kwargs['geometry']['required'])
