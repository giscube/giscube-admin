import hashlib
import json
import os
import shutil

from django.apps import apps
from django.db import connections
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from oauth2_provider.models import get_access_token_model, get_application_model
from rest_framework.test import APITransactionTestCase


UserModel = get_user_model()
ApplicationModel = get_application_model()
AccessTokenModel = get_access_token_model()


class BulkClient(APIClient):
    def post(self, url, data, *args, **kwargs):
        if list(filter(None, url.split('/')))[-1] == 'bulk' and type(data) is dict and 'X_BULK_HASH' not in kwargs:
            if '_META' not in data:
                data['_META'] = {'time': timezone.now().isoformat()}
            body = json.dumps(data, sort_keys=True, separators=(',', ':'))
            if type(body) is str:
                body = body.encode('utf-8')
            hash = hashlib.md5(body).hexdigest()
            kwargs['X_BULK_HASH'] = hash
            kwargs['content_type'] = 'application/json'
            if 'format' in kwargs:
                del kwargs['format']
            return super().generic('POST', url, body, content_type='application/json', X_BULK_HASH=hash)
        else:
            return super().post(url, data, *args, **kwargs)


@override_settings(MEDIA_ROOT='/tmp/giscube')
class BaseTest(APITransactionTestCase):
    def setUp(self):
        self.client = BulkClient()
        self.superuser = UserModel.objects.create_superuser(
            'superuser', 'superuser@example.com', '123456')
        self.test_user = UserModel.objects.create_user(
            'test_user', 'test@example.com', '123456',
            first_name='Test', last_name='User',
            is_staff=True)
        self.dev_user = UserModel.objects.create_user(
            'dev_user', 'dev@example.com', '123456')

        self.application = ApplicationModel(
            name="default_app",
            user=self.dev_user,
            client_type=ApplicationModel.CLIENT_PUBLIC,
            authorization_grant_type=ApplicationModel.GRANT_PASSWORD,
        )
        self.application.save()

    def login_superuser(self):
        url = reverse('oauth2_provider:token')
        response = self.client.post(url, {
            'username': 'superuser',
            'password': '123456',
            'grant_type': 'password',
            'client_id': self.application.client_id})
        content = json.loads(response.content.decode('utf-8'))
        self.token = content['access_token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.token)

    def login_test_user(self):
        url = reverse('oauth2_provider:token')
        response = self.client.post(url, {
            'username': 'test_user',
            'password': '123456',
            'grant_type': 'password',
            'client_id': self.application.client_id})
        content = json.loads(response.content.decode('utf-8'))
        self.token = content['access_token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.token)

    def login_dev_user(self):
        url = reverse('oauth2_provider:token')
        response = self.client.post(url, {
            'username': 'dev_user',
            'password': '123456',
            'grant_type': 'password',
            'client_id': self.application.client_id})
        content = json.loads(response.content.decode('utf-8'))
        self.token = content['access_token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.token)

    def login_user(self, username, password):
        url = reverse('oauth2_provider:token')
        response = self.client.post(url, {
            'username': username,
            'password': password,
            'grant_type': 'password',
            'client_id': self.application.client_id})
        content = json.loads(response.content.decode('utf-8'))
        self.token = content['access_token']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.token)

    def logout(self):
        self.client.credentials(HTTP_AUTHORIZATION='')

    def tearDown(self):
        if 'layerserver_databaselayer' in apps.all_models:
            for x in list(apps.all_models['layerserver_databaselayer'].keys()):
                del apps.all_models['layerserver_databaselayer'][x]
        self.application.delete()
        self.test_user.delete()
        self.dev_user.delete()

        try:
            for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                for f in files:
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    shutil.rmtree(os.path.join(root, d))
        except Exception as e:
            print('Error deleting %s directory' % settings.MEDIA_ROOT)
            print(str(e))

    # def bulk_post(self, url, data):
    #     if '_META' not in data:
    #         data['_META'] = {'time': timezone.now().isoformat()}
    #     body = json.dumps(data, sort_keys=True, separators=(',', ':'))
    #     hash = hashlib.md5(body.encode('utf-8')).hexdigest()
    #     return self.client.generic('POST', url, body, content_type='application/json', X_BULK_HASH=hash)

    # Fix AttributeError: 'function' object has no attribute 'wrapped'
    @classmethod
    def _remove_databases_failures(cls):
        for alias in connections:
            if alias in cls.databases:
                continue
            connection = connections[alias]
            for name, _ in cls._disallowed_connection_methods:
                method = getattr(connection, name)
                try:
                    setattr(connection, name, method.wrapped)
                except Exception:
                    pass
