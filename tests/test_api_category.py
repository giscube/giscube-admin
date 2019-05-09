from django.contrib.auth.models import Permission
from django.test import LiveServerTestCase

from giscube.models import Category
from giscube.utils import get_or_create_category

from tests.common import BaseTest


class APICategoryTestCase(LiveServerTestCase, BaseTest):
    def add_permissions(self):
        codes = ['add_category', 'change_category', 'delete_category', 'view_category']
        permissions = Permission.objects.filter(codename__in=codes)
        self.dev_user.user_permissions.add(*permissions)

    def test_create(self):
        self.login_dev_user()
        server_url = self.live_server_url
        headers = {}
        headers['Authorization'] = 'Bearer %s' % self.token
        parent = Category(name='ParentCategory')
        category = Category(name='Category', parent=parent)
        pk = get_or_create_category(server_url, headers, category)
        self.assertEqual(pk, None)
        self.add_permissions()
        pk = get_or_create_category(server_url, headers, category)
        created = Category.objects.filter(pk=pk).first()
        self.assertEqual(created.name, category.name)
        self.assertEqual(created.parent.name, parent.name)

    def test_get(self):
        self.login_dev_user()
        server_url = self.live_server_url
        headers = {}
        headers['Authorization'] = 'Bearer %s' % self.token
        parent = Category(name='ParentCategory')
        parent.save()
        category = Category(name='Category', parent=parent)
        category.save()
        pk = get_or_create_category(server_url, headers, category)
        self.assertEqual(pk, None)
        self.add_permissions()
        pk = get_or_create_category(server_url, headers, category)
        self.assertEqual(category.pk, pk)
