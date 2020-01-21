import inspect
import json

from django.utils.translation import gettext as _

from .base import BaseJSONWidget


class ForeignKeyWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "dblayer": "layername",
        "to_field": "id",
        "geom": true
    }
    """)
    base_type = 'foreignkey'

    @staticmethod
    def is_valid(cleaned_data):
        from ..models import DataBaseLayer

        value = cleaned_data['widget_options']
        try:
            data = json.loads(value)
        except Exception:
            return _('Invalid JSON format')

        if 'dblayer' not in data:
            return _('\'dblayer\' attribute is required')

        layer = DataBaseLayer.objects.filter(name=data['dblayer']).first()
        if not layer:
            return _('The %s \'dblayer\' doesn\'t exist' % data['dblayer'])

        if 'to_field' not in data:
            return _('\'to_field\' attribute is required')

        to_field = layer.fields.filter(name=data['to_field']).exists()
        if not to_field:
            return _('The %s \'attribute\' doesn\'t exist', data['to_field'])

        if 'geom' in data and not layer.geom_field:
            return _('The %s \'dblayer\' doesn\'t have a geometry column' % data['dblayer'])

    @staticmethod
    def serialize_widget_options(obj):
        try:
            options = json.loads(obj.widget_options)
        except Exception:
            return {'error': 'ERROR PARSING WIDGET OPTIONS'}

        data = {'widget_options': options}
        return data
