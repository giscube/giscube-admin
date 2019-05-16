import inspect
import json

from django.utils.translation import gettext as _

from layerserver.models import DataBaseLayer

from .base import BaseJSONWidget


class Relation1NWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "dblayer": "layername",
        "parent_id": "id",
        "dblayer_id": "parent_id"
    }
    """)

    ERROR_DBLAYER_REQUIRED = _('\'dblayer\' attribute is required')
    ERROR_DBLAYER_NOT_EXISTS = _('\'dblayer\' [%s] doesn\'t exist')
    ERROR_PARENT_ID_REQUIRED = _('\'parent_id\' attribute is required')
    ERROR_PARENT_ID_NOT_EXISTS = _('\'parent_id\' [%s] doesn\'t exist')
    ERROR_DBLAYER_ID_REQUIRED = _('\'dblayer_id\' attribute is required')
    ERROR_DBLAYER_ID_NOT_EXISTS = _('\'parent_id\' [%s] doesn\'t exist')

    @staticmethod
    def is_valid(value):
        try:
            data = json.loads(value)
        except Exception:
            return Relation1NWidget.ERROR_INVALID_JSON

        if 'dblayer' not in data:
            return Relation1NWidget.ERROR_PARENT_ID_REQUIRED

        dblayer = DataBaseLayer.objects.filter(name=data['dblayer']).first()
        if dblayer is None:
            return Relation1NWidget.ERROR_DBLAYER_NOT_EXISTS % data['dblayer']

        if 'parent_id' not in data:
            return Relation1NWidget.ERROR_COLUMN_REQUIRED

        parent_id = dblayer.fields.filter(name=data['parent_id']).first()
        if parent_id is None:
            return Relation1NWidget.ERROR_PARENT_ID__NOT_EXISTS % data['parent_id']

        if 'dblayer_id' not in data:
            return Relation1NWidget.ERROR_DBLAYER_ID_REQUIRED
        dblayer_id = dblayer.fields.filter(name=data['dblayer_id']).first()
        if dblayer_id is None:
            return Relation1NWidget.ERROR_DBLAYER_ID_NOT_EXISTS % data['dblayer_id']

    @staticmethod
    def serialize_widget_options(obj):
        try:
            options = json.loads(obj.widget_options)
        except Exception:
            return {'error': 'ERROR PARSING WIDGET OPTIONS'}

        data = {'widget_options': options}
        return data
