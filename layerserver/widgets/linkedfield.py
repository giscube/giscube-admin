import inspect
import json

from django.utils.translation import gettext as _

from .base import BaseJSONWidget


class LinkedfieldWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "source": "type_id",
        "column": "type_name"
    }
    """)

    def is_valid(value):
        try:
            data = json.loads(value)
        except Exception:
            return _('Invalid JSON format')

        if 'source' not in data:
            return _('\'source\' attribute is required')

        if 'column' not in data:
            return _('\'column\' attribute is required')
