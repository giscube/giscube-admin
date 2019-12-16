from .base import BaseWidget


class ModificationUserWidget(BaseWidget):
    base_type = 'string'

    @staticmethod
    def update(request, instance, validated_data, widget):
        validated_data[widget['name']] = request.user.username

    @staticmethod
    def is_valid(cleaned_data):
        if not cleaned_data['readonly']:
            return ModificationUserWidget.ERROR_READONLY_REQUIRED
