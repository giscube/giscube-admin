import inspect
import json

from django.utils.translation import gettext as _

from .base import BaseJSONWidget


class DateWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "format": "yyyy/mm/dd"
    }
    """)

    ERROR_FORMAT_REQUIRED = _('\'format\' attribute is required')

    @staticmethod
    def is_valid(value):
        try:
            data = json.loads(value)
        except Exception:
            return DateWidget.ERROR_INVALID_JSON

        if 'format' not in data:
            return DateWidget.ERROR_FORMAT_REQUIRED
