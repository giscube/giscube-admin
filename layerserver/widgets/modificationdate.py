from datetime import datetime
from django.utils.timezone import get_current_timezone

from .date import DateWidget


class ModificationDateWidget(DateWidget):
    base_type = 'date'

    @staticmethod
    def update(request, instance, validated_data, widget):
        validated_data[widget['name']] = datetime.now(tz=get_current_timezone()).date()

    @staticmethod
    def is_valid(cleaned_data):
        if not cleaned_data['readonly']:
            return ModificationDateWidget.ERROR_READONLY_REQUIRED
        return DateWidget.is_valid(cleaned_data)
