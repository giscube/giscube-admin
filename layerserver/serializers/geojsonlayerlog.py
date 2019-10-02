import json

from django.utils import formats
from django.utils.translation import gettext as _

from django_celery_results.models import TaskResult
from rest_framework import serializers


class GeoJSONLayerLogSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        old = super().to_representation(obj)
        date_done = ''
        if obj.date_done:
            date_done = formats.date_format(obj.date_done, format='DATETIME_FORMAT', use_l10n=True)
        data = {'task_id': old['task_id'], 'date_done': date_done, 'status': None, 'status_description': ''}
        if obj.status == 'SUCCESS':
            result = None
            try:
                result = json.loads(obj.result)
            except Exception:
                pass
            if result:
                if result['status']:
                    data['status'] = 'generated'
                    data['status_description'] = _('Successfully generated')
                else:
                    data['status'] = 'generated'
                    data['status_description'] = result['error']
        else:
            data['status'] = old['status'].lower()

        return data

    class Meta:
        model = TaskResult
        fields = ['task_id', 'status']
