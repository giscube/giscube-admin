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

    ERROR_SOURCE_REQUIRED = _('\'source\' attribute is required')
    ERROR_COLUMN_REQUIRED = _('\'column\' attribute is required')

    @staticmethod
    def is_valid(value):
        try:
            data = json.loads(value)
        except Exception:
            return LinkedfieldWidget.ERROR_INVALID_JSON

        if 'source' not in data:
            return LinkedfieldWidget.ERROR_SOURCE_REQUIRED

        if 'column' not in data:
            return LinkedfieldWidget.ERROR_COLUMN_REQUIRED
