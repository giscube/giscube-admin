import json

from django.core.exceptions import ValidationError


def validate_options_json_format(value):
    if value is not None:
        obj = None
        try:
            obj = json.loads(value)
        except Exception:
            raise ValidationError('%s must be a valid json format' % value)
        if not isinstance(obj, dict):
            raise ValidationError('%s must be a dictionary' % value)
