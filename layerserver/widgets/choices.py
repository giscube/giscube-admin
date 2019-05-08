from .base import BaseWidget


class ChoicesWidget(BaseWidget):
    TEMPLATE = "key1,value1\nkey2,value2"

    @staticmethod
    def serialize_widget_options(obj):
        data = {}
        try:
            rows = []
            if obj.widget_options is not None:
                for line in obj.widget_options.splitlines():
                    parts = line.split(',')
                    if len(parts) == 1:
                        rows.append(parts[0])
                    elif len(parts) == 2:
                        rows.append(parts)
                    else:
                        return {'error': 'ERROR WITH WIDGET OPTIONS'}
            data['values_list'] = rows
        except Exception:
            return {'error': 'ERROR WITH WIDGET OPTIONS'}

        return {'widget_options': data}
