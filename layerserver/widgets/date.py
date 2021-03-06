import inspect
import json

from django.utils.translation import gettext as _

from .base import BaseJSONWidget


class DateWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "format": "YYYY-MM-DD"
    }
    """)
    ERROR_FORMAT_REQUIRED = _('\'format\' attribute is required')
    base_type = 'date'

    @staticmethod
    def is_valid(cleaned_data):
        value = cleaned_data['widget_options']
        try:
            data = json.loads(value)
        except Exception:
            return DateWidget.ERROR_INVALID_JSON

        if 'format' not in data:
            return DateWidget.ERROR_FORMAT_REQUIRED

    @staticmethod
    def serialize_widget_options(obj):
        if obj.widget_options is None or obj.widget_options == '':
            obj.widget_options = DateWidget.TEMPLATE
        try:
            options = json.loads(obj.widget_options)
        except Exception:
            return {'error': 'ERROR PARSING WIDGET OPTIONS'}

        data = {'widget_options': options}
        return data
