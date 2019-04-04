import json
import os
import shutil
import tempfile

from django.core.files import File
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TransactionTestCase

from django.urls import reverse

from giscube.models import DBConnection
from layerserver.models import DataBaseLayer, DataBaseLayerField
from layerserver.model_legacy import create_dblayer_model
from tests.common import BaseTest

UserModel = get_user_model()


class DataBaseLayerImageWidgetTestCase(BaseTest, TransactionTestCase):
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

        upload_root = os.path.join(tempfile.gettempdir(), 'images')
        if os.path.exists(upload_root):
            shutil.rmtree(upload_root)
        os.makedirs(upload_root)
        self.upload_root = upload_root

        thumbnail_root = os.path.join(tempfile.gettempdir(), 'thumbnails')
        if os.path.exists(thumbnail_root):
            shutil.rmtree(thumbnail_root)
        os.makedirs(thumbnail_root)
        self.thumbnail_root = thumbnail_root

        self.base_url = 'http://localhost/giscube_media/images/'
        self.thumbnail_base_url = 'http://localhost/giscube_media/thumbnails/'

        layer = DataBaseLayer()
        layer.db_connection = conn
        layer.slug = 'imagefield'
        layer.name = 'tests_testimagefield'
        layer.table = 'tests_testimagefield'
        layer.pk_field = 'code'
        layer.geometry_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        layer.refresh_from_db()
        field = layer.fields.filter(name='image').first()
        field.widget = DataBaseLayerField.WIDGET_CHOICES.image
        self.thumbnail_base_url
        options = {
            'upload_root': self.upload_root,
            'thumbnail_root': self.thumbnail_root,
        }
        self.widget_options = options
        field.widget_options = json.dumps(options)
        field.save()

        self.layer = layer

    def tearDown(self):
        try:
            shutil.rmtree(self.upload_root)
        except Exception:
            print('Error while deleting directory')
        try:
            shutil.rmtree(self.thumbnail_root)
        except Exception:
            print('Error while deleting directory')

    def add_test_files(self, files):
        Model = create_dblayer_model(self.layer)
        test_files = []
        i = 0
        for filename in files:
            test_model = Model()
            test_model.code = 'B%s' % i
            test_model.geometry = 'POINT (%s 10)' % i
            path = 'tests/files/%s' % filename
            f = open(path, 'rb')
            test_model.image.save(name=filename, content=File(f))
            test_model.save()
            test_files.append(test_model)
            i += 1
        return test_files

    def test_urls(self):
        self.login_test_user()
        url = reverse('content-list', kwargs={'layer_slug': self.layer.slug})
        path = 'tests/files/giscube_01.png'
        f = open(path, 'rb')
        data = {
            'code': '001',
            'geometry': 'POINT(0 0)',
            'image': f
        }
        response = self.client.post(url, data)
        f.close()
        self.assertEqual(response.status_code, 201)
        result = response.json()

        c = Client()
        response = c.get(result['properties']['image']['src'])
        self.assertEqual(response.status_code, 200)

        c = Client()
        response = c.get(result['properties']['image']['thumbnail'])
        self.assertEqual(response.status_code, 200)
