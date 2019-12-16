from datetime import datetime
from django.utils.timezone import get_current_timezone

from .base import BaseWidget


class CreationDateWidget(BaseWidget):
    base_type = 'date'

    @staticmethod
    def create(request, validated_data, widget):
        validated_data[widget['name']] = datetime.now(tz=get_current_timezone()).date()

    @staticmethod
    def is_valid(cleaned_data):
        if not cleaned_data['readonly']:
            return BaseWidget.ERROR_READONLY_REQUIRED
