from django.utils.translation import gettext as _


class BaseWidget(object):
    TEMPLATE = ""

    def is_valid(value):
        pass


class BaseJSONWidget(object):
    TEMPLATE = "{}"

    ERROR_INVALID_JSON = _('Invalid JSON format')

    @staticmethod
    def is_valid(value):
        pass
