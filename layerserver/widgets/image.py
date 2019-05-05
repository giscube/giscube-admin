import inspect
import json

from django.conf import settings
from django.utils.translation import gettext as _

from .base import BaseJSONWidget


class ImageWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "upload_root": "%simages/",
        "base_url": "%simages/",
        "thumbnail_root": "%sthumbnails/",
        "thumbnail_base_url": "%sthumbnails/"
    }
    """ % (
        settings.MEDIA_ROOT,
        '%s%s' % (settings.GISCUBE_URL, settings.MEDIA_URL.replace(settings.APP_URL, '')),
        settings.MEDIA_ROOT,
        '%s%s' % (settings.GISCUBE_URL, settings.MEDIA_URL.replace(settings.APP_URL, '')),
    ))

    def is_valid(value):
        try:
            data = json.loads(value)
        except Exception:
            return _('Invalid JSON format')

        if 'upload_root' not in data:
            return _('\'upload_root\' attribute is required')
