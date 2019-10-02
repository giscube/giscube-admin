import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.test import Client, TransactionTestCase
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer, DataBaseLayerField
from tests.common import BaseTest


UserModel = get_user_model()


class DataBaseLayerImageWidgetAutoTestCase(BaseTest, TransactionTestCase):
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
        layer.name = 'tests_specie'
        layer.table = 'tests_specie'
        layer.pk_field = 'code'
        layer.geom_field = None
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        layer.refresh_from_db()
        field = layer.fields.filter(name='image').first()
        field.widget = DataBaseLayerField.WIDGET_CHOICES.image
        options = {
            'upload_root': '<auto>',
            'thumbnail_root': '<auto>'
        }
        self.widget_options = options
        field.widget_options = json.dumps(options)
        field.save()

        self.layer = layer

    def add_test_files(self, files):
        Model = create_dblayer_model(self.layer)
        test_files = []
        i = 0
        for filename in files:
            test_model = Model()
            test_model.code = 'B%s' % i
            test_model.name = 'Abies alba'
            path = 'tests/files/%s' % filename
            f = open(path, 'rb')
            test_model.image.save(name=filename, content=File(f))
            test_model.save()
            f.close()
            test_files.append(test_model)
            i += 1
        return test_files

    def test_add_image(self):
        self.login_test_user()
        url = reverse('content-list', kwargs={'name': self.layer.name})
        path = 'tests/files/giscube_01.png'
        f = open(path, 'rb')
        data = {
            'code': '001',
            'name': 'Abies alba',
            'image': f
        }
        response = self.client.post(url, data)
        f.close()
        self.assertEqual(response.status_code, 201)

        Model = create_dblayer_model(self.layer)
        storage = Model._meta.get_field('image').storage
        thumbnail_storage = storage.get_thumbnail_storage()
        self.assertTrue(os.path.isfile(os.path.join(storage.location, 'giscube_01.png')))
        self.assertTrue(
            os.path.isfile(os.path.join(thumbnail_storage.location, '%s.thumbnail.png' % 'giscube_01.png')))

    def test_urls(self):
        self.login_test_user()
        url = reverse('content-list', kwargs={'name': self.layer.name})
        path = 'tests/files/giscube_01.png'
        f = open(path, 'rb')
        data = {
            'code': '001',
            'name': 'Abies alba',
            'image': f
        }
        response = self.client.post(url, data)
        f.close()
        self.assertEqual(response.status_code, 201)
        result = response.json()

        c = Client()
        response = c.get(result['image']['src'])
        self.assertEqual(response.status_code, 200)

        Model = create_dblayer_model(self.layer)
        storage = Model._meta.get_field('image').storage
        thumbnail_storage = storage.get_thumbnail_storage()

        image = result['image']['thumbnail'].split('/')[-1].split('?')[0]
        image_path = os.path.join(thumbnail_storage.location, image)
        self.assertTrue(os.path.exists(image_path))

        c = Client()
        response = c.get(result['image']['thumbnail'])
        self.assertTrue(os.path.exists(image_path))
        self.assertEqual(response.status_code, 200)

        url = reverse('content-list', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        result = response.json()
        self.assertEqual(response.status_code, 200)
        for item in result['data']:
            c = Client()
            response = c.get(item['image']['src'])
            self.assertEqual(response.status_code, 200)

            c = Client()
            response = c.get(item['image']['thumbnail'])
            self.assertEqual(response.status_code, 200)
