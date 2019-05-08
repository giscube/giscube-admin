from .base import BaseWidget


class AutoWidget(BaseWidget):
    TEMPLATE = ""

    @staticmethod
    def serialize_widget_options(obj):
        return {'widget': obj.field_type}
