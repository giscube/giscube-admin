from django.conf import settings
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer
from tests.common import BaseTest


class DataBaseLayerDefaultValueTestCase(BaseTest):
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
        self.conn = conn
        self.sql_to_delete = []

    def test_sequence(self):
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
        with self.conn.get_connection().cursor() as cursor:
            cursor.execute(sql)

        self.sql_to_delete = [
            'DROP TABLE tree;',
            'DROP SEQUENCE tree_code_seq;',
        ]

        layer = DataBaseLayer()
        layer.db_connection = self.conn
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

        Tree = create_dblayer_model(self.layer)
        obj = Tree()
        obj.description = 'test 1'
        obj.save()

        self.assertEqual(Tree.objects.last().code, '1')

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
        self.assertEqual(response.status_code, 200)
        # with ModelFactory(self.layer) as Tree:
        self.assertEqual(Tree.objects.last().code, '2')

    def test_sequence_int(self):
        sql = """
            CREATE SEQUENCE tree_int_code_seq
                START WITH 1
                INCREMENT BY 1
                NO MINVALUE
                NO MAXVALUE
                CACHE 1;
            CREATE TABLE tree_int (
                id SERIAL NOT NULL,
                code integer NOT NULL
                    default (nextval('tree_int_code_seq'::regclass)),
                name character varying(12) default 'Hell")o',
                description character varying(250)
            );
        """
        with self.conn.get_connection().cursor() as cursor:
            cursor.execute(sql)
        self.sql_to_delete = [
            'DROP TABLE tree_int;',
            'DROP SEQUENCE tree_int_code_seq;',
        ]
        layer = DataBaseLayer()
        layer.db_connection = self.conn
        layer.slug = 'tree_int'
        layer.name = 'tree_int'
        layer.table = 'tree_int'
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

        Tree = create_dblayer_model(self.layer)
        obj = Tree()
        obj.description = 'test 1'
        obj.save()

        self.assertEqual(Tree.objects.last().code, 1)

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
        # print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Tree.objects.last().code, 2)

    def tearDown(self):
        with self.conn.get_connection().cursor() as cursor:
            for sql in self.sql_to_delete:
                cursor.execute(sql)
        super().tearDown()
