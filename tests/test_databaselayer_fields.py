import os
import shutil
import tempfile

from unittest import mock

from layerserver import widgets
from tests.common import BaseTest


class DataBaseLayerFieldsValidatorTestCase(BaseTest):
    to_delete = []

    def tearDown(self):
        for f in self.to_delete:
            try:
                if os.path.isdir(f):
                    shutil.rmtree(f)
            except Exception:
                print('Error while deleting directory %s' % f)
        super().tearDown()

    def test_date_field(self):
        field = {'widget_options': ''}
        self.assertEqual(widgets.DateWidget.is_valid(field), widgets.DateWidget.ERROR_INVALID_JSON)
        field = {'widget_options': '{}'}
        self.assertEqual(widgets.DateWidget.is_valid(field), widgets.DateWidget.ERROR_FORMAT_REQUIRED)

    def test_linkedfield(self):
        field = {'widget_options': ''}
        self.assertEqual(widgets.LinkedfieldWidget.is_valid(field), widgets.LinkedfieldWidget.ERROR_INVALID_JSON)
        field = {'widget_options': '{}'}
        self.assertEqual(widgets.LinkedfieldWidget.is_valid(field), widgets.LinkedfieldWidget.ERROR_SOURCE_REQUIRED)
        field = {'widget_options': '{"source": "type_id", "column": "type_name"}'}
        self.assertEqual(widgets.LinkedfieldWidget.is_valid(field), None)

    def test_image(self):
        field = {'widget_options': ''}
        self.assertEqual(widgets.ImageWidget.is_valid(field), widgets.ImageWidget.ERROR_INVALID_JSON)
        field = {'widget_options': '{}'}
        self.assertEqual(widgets.ImageWidget.is_valid(field), widgets.ImageWidget.ERROR_UPLOAD_ROOT_REQUIRED)
        temp_root = tempfile.mkdtemp()
        self.to_delete.append(temp_root)
        upload_root = os.path.join(temp_root, 'images_nok')
        config = '{"upload_root": "%s"}' % upload_root
        field = {'widget_options': config}
        self.assertEqual(widgets.ImageWidget.is_valid(field), widgets.ImageWidget.ERROR_UPLOAD_ROOT_NOT_EXISTS)

        temp_root = tempfile.mkdtemp()
        upload_root = os.path.join(temp_root, 'images_ok')
        config = '{"upload_root": "%s", "base_url": "http//localhost"}' % upload_root
        field = {'widget_options': config}
        os.mkdir(upload_root)
        self.assertTrue(os.path.isdir(upload_root))
        self.assertEqual(widgets.ImageWidget.is_valid(field), widgets.ImageWidget.ERROR_BASE_URL)
        config = '{"upload_root": "%s", "base_url": "http://localhost"}' % upload_root
        field = {'widget_options': config}
        self.assertEqual(widgets.ImageWidget.is_valid(field), None)

        thumbnail_root = os.path.join(temp_root, 'thumbnail_nok')
        config = '{"upload_root": "%s", "base_url": "http://localhost", "thumbnail_root": "%s"}' % (
            upload_root, thumbnail_root)
        field = {'widget_options': config}
        self.assertEqual(widgets.ImageWidget.is_valid(field), widgets.ImageWidget.ERROR_THUMBNAIL_ROOT_NOT_EXISTS)

        thumbnail_root = os.path.join(temp_root, 'thumbnail_ok')
        config = '{"upload_root": "%s", "base_url": "http://localhost", "thumbnail_root": "%s"}' % (
            upload_root, thumbnail_root)
        os.mkdir(thumbnail_root)
        self.assertTrue(os.path.isdir(thumbnail_root))
        config = ('{"upload_root": "%s", "base_url": "http://localhost", "thumbnail_root": "%s",'
                  '"thumbnail_base_url": "http//localhost"}') % (upload_root, thumbnail_root)
        field = {'widget_options': config}
        self.assertEqual(widgets.ImageWidget.is_valid(field), widgets.ImageWidget.ERROR_THUMBNAIL_BASE_URL)

        config = '{"upload_root": "%s", "base_url": "http://localhost"}' % upload_root
        field = {'widget_options': config}
        self.assertEqual(widgets.ImageWidget.is_valid(field), None)

    @mock.patch('layerserver.widgets.image.os.access')
    def test_image_dir_upload_root_not_writable(self, os_access):
        os_access.return_value = False
        temp_root = tempfile.mkdtemp()
        self.to_delete.append(temp_root)
        upload_root = os.path.join(temp_root, 'images_nok')
        config = '{"upload_root": "%s"}' % upload_root
        field = {'widget_options': config}
        os.mkdir(upload_root, 0o444)
        self.assertTrue(os.path.isdir(upload_root))
        self.assertEqual(widgets.ImageWidget.is_valid(field), widgets.ImageWidget.ERROR_UPLOAD_ROOT_NOT_WRITABLE)

    @mock.patch('layerserver.widgets.image.os.access')
    def test_image_dir_thumbnail_root_not_writable(self, os_access):
        temp_root = tempfile.mkdtemp()
        upload_root = os.path.join(temp_root, 'images_ok')
        thumbnail_root = os.path.join(temp_root, 'thumbnail_nok')
        config = '{"upload_root": "%s", "base_url": "http://localhost", "thumbnail_root": "%s"}' % (
            upload_root, thumbnail_root)
        field = {'widget_options': config}
        os.mkdir(upload_root, 0o444)
        os.mkdir(thumbnail_root, 0o444)
        self.assertTrue(os.path.isdir(thumbnail_root))
        os_access.side_effect = lambda dir, check: True if dir == upload_root else False
        self.assertEqual(widgets.ImageWidget.is_valid(field), widgets.ImageWidget.ERROR_THUMBNAIL_ROOT_NOT_WRITABLE)
