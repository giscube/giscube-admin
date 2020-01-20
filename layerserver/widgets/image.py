import inspect
import json
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.validators import URLValidator
from django.utils.translation import gettext as _

from ..fields import ImageWithThumbnailField
from ..storage import get_image_with_thumbnail_storage_class
from .base import BaseJSONWidget


def get_auto_images_root(layer, field_name):
    return os.path.join(settings.MEDIA_ROOT, layer.service_path, 'field_%s' % field_name, 'images')


def get_auto_thumbnails_root(layer, field_name):
    return os.path.join(settings.MEDIA_ROOT, layer.service_path, 'field_%s' % field_name, 'images')


def _get_storage_class(dblayer_field, widget_options):
    """
    'upload_root' must contains the full folder path to avoid folders in the image name.
    That's why upload_to is not used.
    """
    if 'upload_root' in widget_options:
        upload_root = widget_options['upload_root']
        base_url = widget_options.get('base_url', None)
        thumbnail_root = widget_options.get('thumbnail_root', None)
        thumbnail_base_url = widget_options.get('thumbnail_base_url', None)
        if upload_root == '<auto>':
            upload_root = get_auto_images_root(dblayer_field.layer, dblayer_field.name)
            base_url = None
        if thumbnail_root == '<auto>':
            thumbnail_root = get_auto_thumbnails_root(dblayer_field.layer, dblayer_field.name)
            thumbnail_base_url = None
        StorageClass = get_image_with_thumbnail_storage_class()
        storage = StorageClass(
            location=upload_root,
            base_url=base_url,
            thumbnail_location=thumbnail_root,
            thumbnail_base_url=thumbnail_base_url,
            thumbnail_width=widget_options.get('thumbnail_width', None),
            thumbnail_height=widget_options.get('thumbnail_height', None)
        )
        storage.save_thumbnail_enabled = thumbnail_root is not None
        return storage


class ImageWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "upload_root": "<auto>",
        "base_url": "<auto>",
        "thumbnail_root": "<auto>",
        "thumbnail_base_url": "<auto>"
    }
    """)

    ERROR_UPLOAD_ROOT_REQUIRED = _('\'upload_root\' attribute is required')
    ERROR_UPLOAD_ROOT_NOT_EXISTS = _('\'upload_root\' folder doesn\'t exist')
    ERROR_UPLOAD_ROOT_NOT_WRITABLE = _('\'upload_root\' folder is not writable')
    ERROR_BASE_URL = _('\'base_url\' is not valid')
    ERROR_THUMBNAIL_ROOT_NOT_EXISTS = _('\'thumbnail_root\' folder doesn\'t exist')
    ERROR_THUMBNAIL_ROOT_NOT_WRITABLE = _('\'thumbnail_root\' folder is not writable')
    ERROR_THUMBNAIL_BASE_URL = _('\'thumbnail_base_url\' is not valid')
    base_type = 'image'

    @staticmethod
    def apply(field_definition, dblayer_field, ctx):
        widget_options = json.loads(dblayer_field.widget_options)
        fixed_kwargs = field_definition['kwargs'].copy()
        fixed_kwargs.update({
            'widget_options': widget_options,
            'storage': _get_storage_class(dblayer_field, widget_options)
        })
        return ImageWithThumbnailField(**fixed_kwargs)

    @staticmethod  # noqa: C901
    def is_valid(cleaned_data):
        value = cleaned_data['widget_options']
        try:
            data = json.loads(value)
        except Exception:
            return ImageWidget.ERROR_INVALID_JSON

        if 'upload_root' not in data:
            return ImageWidget.ERROR_UPLOAD_ROOT_REQUIRED

        base_url = data.get('base_url', None)
        thumbnail_root = data.get('thumbnail_root', None)
        thumbnail_base_url = data.get('thumbnail_base_url', None)
        StorageClass = get_image_with_thumbnail_storage_class()
        if data['upload_root'] != '<auto>':
            storage = StorageClass(
                location=data['upload_root'],
                base_url=base_url,
                thumbnail_location=thumbnail_root,
                thumbnail_base_url=thumbnail_base_url
            )
            try:
                storage.listdir('.')
            except OSError:
                return ImageWidget.ERROR_UPLOAD_ROOT_NOT_EXISTS

            if issubclass(StorageClass, FileSystemStorage):
                path = storage.path('.')
                if not os.access(path, os.W_OK):
                    return ImageWidget.ERROR_UPLOAD_ROOT_NOT_WRITABLE

        if base_url is not None and base_url != '<auto>':
            val = URLValidator()
            try:
                val(base_url)
            except ValidationError:
                return ImageWidget.ERROR_BASE_URL

        if thumbnail_root is not None and thumbnail_root != '<auto>':
            thumbnail_storage = storage.get_thumbnail_storage()
            try:
                thumbnail_storage.listdir('.')
            except OSError:
                return ImageWidget.ERROR_THUMBNAIL_ROOT_NOT_EXISTS

            if issubclass(thumbnail_storage.__class__, FileSystemStorage):
                path = thumbnail_storage.path('.')
                if not os.access(path, os.W_OK):
                    return ImageWidget.ERROR_THUMBNAIL_ROOT_NOT_WRITABLE

        if thumbnail_base_url is not None and thumbnail_base_url != '<auto>':
            val = URLValidator()
            try:
                val(thumbnail_base_url)
            except ValidationError:
                return ImageWidget.ERROR_THUMBNAIL_BASE_URL

    @staticmethod
    def serialize_widget_options(obj):
        try:
            options = json.loads(obj.widget_options)
        except Exception:
            return {'error': 'ERROR PARSING WIDGET OPTIONS'}

        widget_options = {}
        if 'upload_size' in options:
            widget_options['upload_size'] = options['upload_size']
        data = {'widget_options': widget_options}
        return data
