from giscube.utils import url_slash_join

from tests.common import BaseTest


class URLSlashJoinTestCase(BaseTest):
    def test_urls(self):
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
