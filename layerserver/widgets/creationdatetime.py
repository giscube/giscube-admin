from datetime import datetime

from django.utils.timezone import get_current_timezone

from .datetime import DatetimeWidget


class CreationDatetimeWidget(DatetimeWidget):
    base_type = 'datetime'

    @staticmethod
    def create(request, validated_data, widget):
        validated_data[widget['name']] = datetime.now(tz=get_current_timezone())

    @staticmethod
    def is_valid(cleaned_data):
        if not cleaned_data['readonly']:
            return CreationDatetimeWidget.ERROR_READONLY_REQUIRED
        return DatetimeWidget.is_valid(cleaned_data)
