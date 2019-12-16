from .base import BaseWidget


class CreationUserWidget(BaseWidget):
    base_type = 'string'

    @staticmethod
    def create(request, validated_data, widget):
        validated_data[widget['name']] = request.user.username

    @staticmethod
    def is_valid(cleaned_data):
        if not cleaned_data['readonly']:
            return BaseWidget.ERROR_READONLY_REQUIRED
