import inspect
import json

from django.utils.translation import gettext as _

from .base import BaseJSONWidget


class SqlchoicesWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "query": "select code, name from types",
        "label": "{code} - {name}",
        "table_headers": [{"code":"Code"}, {"name": "Name"}]
    }
    """)
    base_type = 'sqlchoices'

    @staticmethod
    def is_valid(cleaned_data):
        value = cleaned_data['widget_options']
        try:
            data = json.loads(value)
        except Exception:
            return _('Invalid JSON format')

        if 'query' not in data:
            return _('\'query\' attribute is required')

    @staticmethod
    def serialize_widget_options(obj):
        data = {}
        headers = []
        rows = []
        try:
            options = json.loads(obj.widget_options)
        except Exception:
            return {'error': 'ERROR PARSING WIDGET OPTIONS'}
        try:
            with obj.layer.db_connection.get_connection().cursor() as cursor:
                query = options['query'].encode('utf-8').decode('unicode_escape')
                cursor.execute('%s LIMIT 0' % query)
                for header in cursor.description:
                    headers.append(header.name)
                cursor.execute(query)
                for r in cursor.fetchall():
                    if len(r) == 1:
                        rows.append(r[0])
                    else:
                        rows.append(r)
        except Exception:
            return {'error': 'ERROR WITH WIDGET OPTIONS'}

        data['values_list_headers'] = headers
        data['values_list'] = rows
        if 'table_headers' in options:
            data['table_headers'] = options['table_headers']
        if 'label' in options:
            data['label'] = options['label']

        return {'widget_options': data}
