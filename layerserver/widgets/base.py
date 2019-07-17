from django.utils.translation import gettext as _


class BaseWidget(object):
    TEMPLATE = ""
    base_type = 'base'

    @staticmethod
    def is_valid(value):
        pass

    @staticmethod
    def serialize_widget_options(obj):
        return {}


class BaseJSONWidget(BaseWidget):
    TEMPLATE = "{}"

    ERROR_INVALID_JSON = _('Invalid JSON format')
