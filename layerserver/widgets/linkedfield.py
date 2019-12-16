import inspect
import json

from django.utils.translation import gettext as _

from .base import BaseJSONWidget


class LinkedfieldWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "source": "type_id"
    }
    """)

    ERROR_SOURCE_REQUIRED = _('\'source\' attribute is required')
    base_type = 'linkedfield'

    @staticmethod
    def is_valid(cleaned_data):
        value = cleaned_data['widget_options']
        try:
            data = json.loads(value)
        except Exception:
            return LinkedfieldWidget.ERROR_INVALID_JSON

        if 'source' not in data:
            return LinkedfieldWidget.ERROR_SOURCE_REQUIRED

    @staticmethod
    def serialize_widget_options(obj):
        try:
            options = json.loads(obj.widget_options)
        except Exception:
            return {'error': 'ERROR PARSING WIDGET OPTIONS'}

        data = {'widget_options': options}
        return data
