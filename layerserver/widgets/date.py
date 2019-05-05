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

    def is_valid(value):
        try:
            data = json.loads(value)
        except Exception:
            return _('Invalid JSON format')

        if 'format' not in data:
            return _('\'format\' attribute is required')
