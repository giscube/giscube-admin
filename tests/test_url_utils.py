from django.test.utils import override_settings

from giscube.utils import remove_app_url, url_slash_join
from tests.common import BaseTest


@override_settings(APP_URL='/apps/giscube/')
class URLUtilsTestCase(BaseTest):
    def test_url_slash_join(self):
        url = url_slash_join('http://localhost/apps/giscube', 'imageserver/services/streets')
        url_ok = 'http://localhost/apps/giscube/imageserver/services/streets'
        self.assertEqual(url, url_ok)

        url = url_slash_join('http://localhost/apps/giscube/', 'imageserver/services/streets')
        url_ok = 'http://localhost/apps/giscube/imageserver/services/streets'
        self.assertEqual(url, url_ok)

        url = url_slash_join('http://localhost/apps/giscube', '/imageserver/services/streets')
        url_ok = 'http://localhost/apps/giscube/imageserver/services/streets'
        self.assertEqual(url, url_ok)

        url = url_slash_join('http://localhost/apps/giscube/', '/imageserver/services/streets')
        url_ok = 'http://localhost/apps/giscube/imageserver/services/streets'
        self.assertEqual(url, url_ok)

        url = url_slash_join('http://localhost/apps/giscube/', '/imageserver/services/streets/')
        url_ok = 'http://localhost/apps/giscube/imageserver/services/streets/'
        self.assertEqual(url, url_ok)

        url = url_slash_join('http://localhost/', '/apps/giscube/', '/imageserver/services/streets')
        url_ok = 'http://localhost/apps/giscube/imageserver/services/streets'
        self.assertEqual(url, url_ok)

        url = url_slash_join('http://localhost/', '', '/apps/giscube/', '/imageserver/services/streets')
        url_ok = 'http://localhost/apps/giscube/imageserver/services/streets'
        self.assertEqual(url, url_ok)

    def test_remove_app_url(self):
        url = remove_app_url('/apps/giscube/imageserver/services/streets')
        self.assertEqual(url, 'imageserver/services/streets')
