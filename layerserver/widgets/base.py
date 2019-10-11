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

    @staticmethod
    def serialize_value(model_obj, field):
        pass

    @staticmethod
    def get_queryset(qs, field, request):
        return qs


class BaseJSONWidget(BaseWidget):
    TEMPLATE = "{}"

    ERROR_INVALID_JSON = _('Invalid JSON format')
