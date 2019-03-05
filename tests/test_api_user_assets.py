import os
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.test.utils import override_settings
from django.urls import reverse

from giscube.models import UserAsset
from rest_framework import status
from rest_framework.test import APITestCase


UserModel = get_user_model()


@override_settings(DEBUG=True)
class ApiUserAssetsTests(APITestCase):

    def login(self):
        self.client.login(username='admin', password='admin')

    def setUp(self):
        self.admin_user = UserModel.objects.create_superuser('admin', '', 'admin')
        self.other = UserModel.objects.create_user('other', '', 'other')

    def tearDown(self):
        UserModel.objects.all().delete()
        UserAsset.objects.all().delete()
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'user/assets/'))

    def test_list(self):
        self.login()
        files = ['2210571.jpg', 'images.docx', 'rgba1px.png']
        assets = {}
        for file in files:
            path = 'tests/files/%s' % file
            f = open(path, 'rb')
            asset = UserAsset()
            asset.user = self.admin_user
            asset.file.save(name=file, content=File(f))
            asset.save()
            assets[str(asset.uuid)] = asset
            f.close()

        url = reverse('user_assets-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(files))

        for file in response.data:
            self.assertTrue(str(file['uuid']) in list(assets.keys()))
            parts = file['file'].split('/')
            self.assertTrue(parts[-1] in files)
            self.assertTrue(parts[-2] in list(assets.keys()))

        asset_key = list(assets.keys())[0]
        url = reverse('user_assets-detail', args=[asset_key])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        file = response.data
        self.assertTrue(str(file['uuid']) in list(assets.keys()))
        parts = file['file'].split('/')
        self.assertTrue(parts[-1] in files)
        self.assertTrue(parts[-2] in list(assets.keys()))
        response = self.client.get(file['url'])
        file_name = file['url'].split('/')[-1]
        self.assertTrue(file['file'].startswith('media://user/assets/%s/' % self.admin_user.pk))
        self.assertTrue(file['file'].endswith(file_name))

    def test_post_image(self):
        self.login()
        url = reverse('user_assets-list')
        path = 'tests/files/2210571.jpg'
        f = open(path, 'rb')
        data = {'file': f}
        response = self.client.post(url, data)
        f.close()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        file = response.data
        response = self.client.get(file['url'])
        file_name = file['url'].split('/')[-1]
        folder = UserAsset.objects.first().uuid
        self.assertEqual(file['file'], 'media://user/assets/%s/%s/%s' % (self.admin_user.pk, folder, file_name))

    def test_delete(self):
        self.login()
        name = '2210571.jpg'
        path = 'tests/files/%s' % name
        f = open(path, 'rb')
        asset = UserAsset()
        asset.user = self.admin_user
        asset.file.save(name=name, content=File(f))
        asset.save()
        f.close()
        self.assertTrue(os.path.exists(asset.file.path))
        url = reverse('user_assets-detail', args=[str(asset.uuid)])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(not os.path.exists(asset.file.path))
        parent_folder = os.path.dirname(asset.file.path)
        self.assertTrue(not os.path.exists(parent_folder))

    def test_permissions(self):
        name = '2210571.jpg'
        path = 'tests/files/%s' % name
        f = open(path, 'rb')
        asset = UserAsset()
        asset.user = self.other
        asset.file.save(name=name, content=File(f))
        asset.save()
        f.close()

        self.client.login(username='other', password='other')
        self.assertTrue(os.path.exists(asset.file.path))
        url_detail = reverse('user_assets-detail', args=[str(asset.uuid)])
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url_file = response.data['url']
        response = self.client.get(url_file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.logout()

        self.login()
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(url_file)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
