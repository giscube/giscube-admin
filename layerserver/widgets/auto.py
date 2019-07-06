from .base import BaseWidget


class AutoWidget(BaseWidget):
    TEMPLATE = ""
    base_type = 'auto'

    @staticmethod
    def serialize_widget_options(obj):
        return {'widget': obj.field_type}
