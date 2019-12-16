from django.utils.translation import gettext as _


class BaseWidget(object):
    ERROR_READONLY_REQUIRED = _('\'readonly\' attribute must be checked')
    TEMPLATE = ""
    base_type = 'base'

    @staticmethod
    def create(request, validated_data, widget):
        pass

    @staticmethod
    def is_valid(cleaned_data):
        """
        admin validation
        """
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

    @staticmethod
    def update(request, instance, validated_data, widget):
        pass


class BaseJSONWidget(BaseWidget):
    TEMPLATE = "{}"

    ERROR_INVALID_JSON = _('Invalid JSON format')
