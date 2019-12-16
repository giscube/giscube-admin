import inspect
import json

from django.utils.translation import gettext as _

from giscube.db.utils import get_table_parts

from .base import BaseJSONWidget


class DisctintValuesWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "allow_add_new": true
    }
    """)
    ERROR_VALUES = _('Allowed values for \'allow_add_new\' are: true, false')
    base_type = 'choices'

    @staticmethod
    def is_valid(cleaned_data):
        value = cleaned_data['widget_options']
        try:
            data = json.loads(value)
        except Exception:
            return DisctintValuesWidget.ERROR_INVALID_JSON

        if 'allow_add_new' in data and type(data['allow_add_new']) != bool:
            return DisctintValuesWidget.ERROR_VALUES

    @staticmethod
    def serialize_widget_options(obj):
        table_parts = get_table_parts(obj.layer.table)
        table_name = table_parts['fixed']
        field = obj.name
        data = {}
        rows = []
        try:
            options = json.loads(obj.widget_options)
        except Exception:
            return {'error': 'ERROR PARSING WIDGET OPTIONS'}
        try:
            with obj.layer.db_connection.get_connection().cursor() as cursor:
                query = 'SELECT DISTINCT %s FROM %s ORDER BY %s' % (field, table_name, field)
                cursor.execute(query)
                nulls = False
                for r in cursor.fetchall():
                    value = r[0]
                    if nulls is False and value is None:
                        nulls = True
                        rows.insert(0, None)
                    else:
                        rows.append(r[0])
        except Exception as e:
            return {'error': 'ERROR WITH WIDGET OPTIONS', 'e': str(e)}
        data['values_list'] = rows
        data['allow_add_new'] = options['allow_add_new'] if 'allow_add_new' in options else True

        return {'widget_options': data}
