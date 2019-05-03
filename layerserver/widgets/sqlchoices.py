import inspect
import json

from django.utils.translation import gettext as _

from .base import BaseJSONWidget


class SqlchoicesWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "query": "select code, name from types",
        "label": "{code} - {name}",
        "headers": ["Code", "Name"]
    }
    """)

    def is_valid(value):
        try:
            data = json.loads(value)
        except Exception:
            return _('Invalid JSON format')

        if 'source' not in data:
            return _('\'query\' attribute is required')
