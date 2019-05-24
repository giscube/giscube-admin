import os
import shutil
import tempfile

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

    def test_date_field(self):
        self.assertEqual(widgets.DateWidget.is_valid(''), widgets.DateWidget.ERROR_INVALID_JSON)
        self.assertEqual(widgets.DateWidget.is_valid('{}'), widgets.DateWidget.ERROR_FORMAT_REQUIRED)

    def test_linkedfield(self):
        self.assertEqual(widgets.LinkedfieldWidget.is_valid(''), widgets.LinkedfieldWidget.ERROR_INVALID_JSON)
        self.assertEqual(widgets.LinkedfieldWidget.is_valid('{}'), widgets.LinkedfieldWidget.ERROR_SOURCE_REQUIRED)
        self.assertEqual(widgets.LinkedfieldWidget.is_valid('{"source": "type_id", "column": "type_name"}'), None)

    def test_image(self):
        self.assertEqual(widgets.ImageWidget.is_valid(''), widgets.ImageWidget.ERROR_INVALID_JSON)
        self.assertEqual(widgets.ImageWidget.is_valid('{}'), widgets.ImageWidget.ERROR_UPLOAD_ROOT_REQUIRED)
        temp_root = tempfile.mkdtemp()
        self.to_delete.append(temp_root)
        upload_root = os.path.join(temp_root, 'images_nok')
        config = '{"upload_root": "%s"}' % upload_root
        self.assertEqual(widgets.ImageWidget.is_valid(config), widgets.ImageWidget.ERROR_UPLOAD_ROOT_NOT_EXISTS)
        os.mkdir(upload_root, 0o444)
        self.assertTrue(os.path.isdir(upload_root))
        self.assertEqual(widgets.ImageWidget.is_valid(config), widgets.ImageWidget.ERROR_UPLOAD_ROOT_NOT_WRITABLE)

        upload_root = os.path.join(temp_root, 'images_ok')
        config = '{"upload_root": "%s", "base_url": "http//localhost"}' % upload_root
        os.mkdir(upload_root)
        self.assertTrue(os.path.isdir(upload_root))
        self.assertEqual(widgets.ImageWidget.is_valid(config), widgets.ImageWidget.ERROR_BASE_URL)
        config = '{"upload_root": "%s", "base_url": "http://localhost"}' % upload_root
        self.assertEqual(widgets.ImageWidget.is_valid(config), None)

        thumbnail_root = os.path.join(temp_root, 'thumbnail_nok')
        config = '{"upload_root": "%s", "base_url": "http://localhost", "thumbnail_root": "%s"}' % (
            upload_root, thumbnail_root)
        self.assertEqual(widgets.ImageWidget.is_valid(config), widgets.ImageWidget.ERROR_THUMBNAIL_ROOT_NOT_EXISTS)

        os.mkdir(thumbnail_root, 0o444)
        self.assertTrue(os.path.isdir(thumbnail_root))
        self.assertEqual(widgets.ImageWidget.is_valid(config), widgets.ImageWidget.ERROR_THUMBNAIL_ROOT_NOT_WRITABLE)

        thumbnail_root = os.path.join(temp_root, 'thumbnail_ok')
        config = '{"upload_root": "%s", "base_url": "http://localhost", "thumbnail_root": "%s"}' % (
            upload_root, thumbnail_root)
        os.mkdir(thumbnail_root)
        self.assertTrue(os.path.isdir(thumbnail_root))
        config = ('{"upload_root": "%s", "base_url": "http://localhost", "thumbnail_root": "%s",'
                  '"thumbnail_base_url": "http//localhost"}') % (upload_root, thumbnail_root)
        self.assertEqual(widgets.ImageWidget.is_valid(config), widgets.ImageWidget.ERROR_THUMBNAIL_BASE_URL)

        config = '{"upload_root": "%s", "base_url": "http://localhost"}' % upload_root
        self.assertEqual(widgets.ImageWidget.is_valid(config), None)
