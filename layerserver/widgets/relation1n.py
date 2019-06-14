import inspect
import json

from django.utils.translation import gettext as _

from .base import BaseJSONWidget


class Relation1NWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "dblayer": "layername",
        "to_field": "id",
        "dblayer_fk": "parent_id"
    }
    """)

    ERROR_DBLAYER_REQUIRED = _('\'dblayer\' attribute is required')
    ERROR_TO_FIELD_REQUIRED = _('\'to_field\' attribute is required')
    ERROR_DBLAYER_FK_REQUIRED = _('\'dblayer_fk\' attribute is required')

    @staticmethod
    def is_valid(value):
        try:
            data = json.loads(value)
        except Exception:
            return Relation1NWidget.ERROR_INVALID_JSON

        if 'dblayer' not in data:
            return Relation1NWidget.ERROR_DBLAYER_REQUIRED

        if 'to_field' not in data:
            return Relation1NWidget.ERROR_TO_FIELD_REQUIRED

        if 'dblayer_fk' not in data:
            return Relation1NWidget.ERROR_DBLAYER_FK_REQUIRED

    @staticmethod
    def serialize_widget_options(obj):
        try:
            options = json.loads(obj.widget_options)
        except Exception:
            return {'error': 'ERROR PARSING WIDGET OPTIONS'}

        data = {'widget_options': options}
        return data
