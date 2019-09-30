import os

from django.contrib.auth import get_user_model
from django.core.files import File
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse

from rest_framework import status

from giscube.models import UserAsset

from .common import BaseTest


UserModel = get_user_model()


@override_settings(DEBUG=True)
class ApiUserAssetsTests(BaseTest):

    def tearDown(self):
        UserModel.objects.all().delete()
        UserAsset.objects.all().delete()
        super().tearDown()

    def test_list(self):
        self.login_superuser()
        files = ['2210571.jpg', 'images.docx', 'rgba1px.png']
        assets = {}
        for file in files:
            path = 'tests/files/%s' % file
            f = open(path, 'rb')
            asset = UserAsset()
            asset.user = self.superuser
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
        file_name = file['url'].split('/')[-1].split('?')[0]
        self.assertTrue(file['file'].startswith('media://user/assets/%s/' % self.superuser.pk))
        self.assertTrue(file['file'].endswith(file_name))

    def test_post_image(self):
        self.login_superuser()
        url = reverse('user_assets-list')
        path = 'tests/files/2210571.jpg'
        f = open(path, 'rb')
        data = {'file': f}
        response = self.client.post(url, data)
        f.close()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        file = response.data
        response = self.client.get(file['url'])
        file_name = file['url'].split('/')[-1].split('?')[0]
        folder = UserAsset.objects.first().uuid
        self.assertEqual(file['file'], 'media://user/assets/%s/%s/%s' % (self.superuser.pk, folder, file_name))

    def test_delete(self):
        self.login_superuser()
        name = '2210571.jpg'
        path = 'tests/files/%s' % name
        f = open(path, 'rb')
        asset = UserAsset()
        asset.user = self.superuser
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
        asset.user = self.test_user
        asset.file.save(name=name, content=File(f))
        asset.save()
        f.close()

        self.login_test_user()
        self.assertTrue(os.path.exists(asset.file.path))
        url_detail = reverse('user_assets-detail', args=[str(asset.uuid)])
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url_file = response.data['url']
        response = self.client.get(url_file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        c = Client()
        response = c.get(url_file.split('?')[0])
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = c.get(url_file)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.logout()

        self.login_dev_user()
        response = self.client.get(url_file)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
