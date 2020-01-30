import json
import os
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.test import TransactionTestCase
from django.urls import reverse

from giscube.models import DBConnection, UserAsset
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer, DataBaseLayerField
from tests.common import BaseTest


UserModel = get_user_model()


class DataBaseLayerImageWidgetNogeomTestCase(BaseTest, TransactionTestCase):
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
            'base_url': self.base_url,
            'upload_root': self.upload_root,
            'thumbnail_root': self.thumbnail_root,
            'thumbnail_base_url': self.thumbnail_base_url
        }
        self.widget_options = options
        field.widget_options = json.dumps(options)
        field.save()

        self.layer = layer

    def tearDown(self):
        super().tearDown()
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
        result = response.json()
        self.assertTrue(os.path.isfile(os.path.join(self.upload_root, 'giscube_01.png')))
        self.assertEqual(result['image']['src'], '%s%s' % (self.base_url, 'giscube_01.png'))
        self.assertEqual(result['image']['thumbnail'], '%s%s.thumbnail.png' % (
            self.thumbnail_base_url, 'giscube_01.png'))

    def test_update_image(self):
        test_files = self.add_test_files(['giscube_01.png'])
        image_path = test_files[0].image.path
        self.assertTrue(os.path.exists(image_path))
        path = 'tests/files/giscube_02.png'
        f = open(path, 'rb')
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': test_files[0].code})
        data = {
            'image': f
        }
        response = self.client.patch(url, data)
        f.close()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(os.path.exists(image_path))

    def test_delete_image(self):
        test_files = self.add_test_files(['giscube_01.png'])
        image_path = test_files[0].image.path
        self.assertTrue(os.path.exists(image_path))
        url = reverse('content-detail', kwargs={'name': self.layer.name, 'pk': test_files[0].code})
        data = {
            'image': None
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(os.path.exists(image_path))

    def test_bulk_images(self):
        self.login_test_user()

        Model = create_dblayer_model(self.layer)
        test_files = self.add_test_files(['giscube_01.png', 'bad name.jpg', 'giscube_02.png', 'giscube_03.png'])

        self.assertTrue(os.path.exists(test_files[1].image.path))
        thumbnail = test_files[1].image.storage.get_thumbnail(test_files[1].image.name)
        self.assertTrue(os.path.exists(thumbnail['path']))
        self.assertEqual('%s%s' % (self.thumbnail_base_url, 'bad_name.jpg.thumbnail.png'), thumbnail['url'])

        url = reverse('user_assets-list')
        files = ['2210571.jpg', 'giscube_01.png']
        assets = {}
        for filename in files:
            path = 'tests/files/%s' % filename
            f = open(path, 'rb')
            data = {'file': f}
            response = self.client.post(url, data)
            f.close()
            assets[filename] = response.data

        image_to_update = Model.objects.get(code='B1').image.path
        self.assertTrue(os.path.exists(image_to_update))
        images_to_delete = Model.objects.get(code=test_files[2].code).image.path
        self.assertTrue(os.path.exists(images_to_delete))
        data = {
            'ADD': [
                {
                    'code': 'C1',
                    'name': 'Abies alba',
                    'image': assets['2210571.jpg']['file']
                }
            ],
            'UPDATE': [
                {
                    'code': 'B2',
                    'image': None
                },
                {
                    'code': 'B1',
                    'name': 'Bur Oak',
                    'image': assets['giscube_01.png']['file']
                },
            ],
            'DELETE': [
                test_files[3].code
            ]
        }

        url = reverse('content-bulk', kwargs={'name': self.layer.name})
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)

        obj = Model.objects.get(code='C1')
        self.assertTrue(os.path.exists(obj.image.path))
        self.assertTrue(obj.image.name.endswith('2210571.jpg'))

        obj = Model.objects.get(code='B1')
        self.assertEqual(obj.name, 'Bur Oak')
        self.assertTrue(os.path.exists(obj.image.path))
        self.assertFalse(obj.image.name.endswith('giscube_01.png'))
        self.assertTrue('giscube_01' in obj.image.name)
        self.assertFalse(os.path.exists(image_to_update))

        self.assertTrue(Model.objects.filter(code=test_files[3].code).first() is None)
        self.assertFalse(os.path.exists(images_to_delete))

        dirs, files = Model._meta.get_field('image').storage.listdir('.')
        self.assertEqual(len(files), 3)
        for f in files:
            name = f.split('.')[0]
            self.assertTrue('giscube_01' in name or 'bad_name' in name or '2210571' in name)

        dirs, files = Model._meta.get_field('image').storage.get_thumbnail_storage().listdir('.')
        self.assertEqual(len(files), 3)
        for f in files:
            name = f.split('.')[0]
            self.assertTrue('giscube_01' in name or 'bad_name' in name or '2210571' in name)
            f.endswith('.thumbnail.png')

        self.assertEqual(UserAsset.objects.all().count(), 0)

    def test_list(self):
        self.login_test_user()
        images = ['giscube_01.png', 'giscube_02.png', 'giscube_03.png']
        self.add_test_files(images)
        url = reverse('content-list', kwargs={'name': self.layer.name})
        response = self.client.get(url)
        result = response.json()
        self.assertEqual(3, result['count'])
        done = []
        for x in result['data']:
            image = x['image']['src'].split('/')[-1]
            self.assertTrue(image in images)
            done.append(image)
        images.sort()
        done.sort()
        self.assertEqual(images, done)
