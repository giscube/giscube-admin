from django.conf import settings
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import ModelFactory
from layerserver.models import DataBaseLayer
from tests.common import BaseTest


class DataBaseLayerDefaultValueTestCase(BaseTest):
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
        self.conn = conn

        sql = """
            CREATE SEQUENCE tree_code_seq
                START WITH 1
                INCREMENT BY 1
                NO MINVALUE
                NO MAXVALUE
                CACHE 1;
            CREATE TABLE tree (
                id SERIAL NOT NULL,
                code character varying(12) NOT NULL
                    default (nextval('tree_code_seq'::regclass))::character varying,
                name character varying(12) default 'Hell")o',
                description character varying(250)
            );
        """
        with conn.get_connection().cursor() as cursor:
            cursor.execute(sql)

        layer = DataBaseLayer()
        layer.db_connection = conn
        layer.slug = 'tree'
        layer.name = 'tree'
        layer.table = 'tree'
        layer.pk_field = 'id'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

        field = self.layer.fields.filter(name='code').first()
        field.blank = True
        field.save()

    def test_sequence(self):
        with ModelFactory(self.layer) as Tree:
            obj = Tree()
            obj.description = 'test 1'
            obj.save()

            obj.refresh_from_db()
            self.assertEqual(obj.code, '1')

        data = {
            'ADD': [
                {
                    'description': 'test 2'
                },
            ],
            'UPDATE': [],
            'DELETE': []
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 204)
        with ModelFactory(self.layer) as Tree:
            self.assertEqual(Tree.objects.last().code, '2')

    def tearDown(self):
        sqls = ['DROP TABLE tree;', 'DROP SEQUENCE tree_code_seq']
        with self.conn.get_connection().cursor() as cursor:
            for sql in sqls:
                cursor.execute(sql)
        super().tearDown()
