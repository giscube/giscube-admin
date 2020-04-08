import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_str

from .utils import remove_accents


class BaseIndex(object):
    pass


class BaseModelIndex(object):
    def __init__(self, context):
        self.context = context

    def get_index(self):
        return self.context.get('index', 'documentindex')

    def get_value(self, obj, field):
        attrs = field.split('.')
        value = obj
        for attr in attrs:
            if value:
                try:
                    value = getattr(value, attr)
                except ObjectDoesNotExist:
                    value = None
                    break
                else:
                    value = self.fix_data_value(value)
            else:
                break
        return value

    def fix_data_value(self, value):
        if value:
            if isinstance(value, (datetime.datetime, datetime.date)):
                value = value.isoformat()
        return value

    def get_context(self):
        return self.context

    def get_content_type(self):
        content_type = self.context.get('content_type')
        if not content_type:
            content_type = '%s.%s' % (self.get_model()._meta.app_label, self.get_model()._meta.model_name)
        return content_type

    def get_config_object_id(self):
        return self.get_context().get('pk_field', 'id')

    def prepare_object_id(self, obj):
        return force_str(getattr(obj, self.get_config_object_id()))

    def get_config_fields(self):
        return self.get_context().get('fields', [])

    def prepare_body(self, obj):
        body = []
        for field in self.get_config_fields():
            value = self.get_value(obj, field)
            if value:
                value = remove_accents(force_str(value))
                body.append(value)
        return body

    def get_config_output_data(self):
        return self.get_context().get('output_data', [])

    def get_config_output_data_keys(self):
        return self.get_context().get('output_data_keys', self.get_config_output_data())

    def _fields_to_dict(self, obj, fields, labels):
        field_labels = {fields[i]: labels[i] for i in range(len(fields))}
        obj_data = {}
        for field in fields:
            value = self.get_value(obj, field)
            obj_data[field_labels[field]] = value
        return obj_data

    def prepare_output_data(self, obj):
        fields = self.get_config_output_data()
        keys = self.get_config_output_data_keys()
        return self._fields_to_dict(obj, fields, keys)

    def get_config_search_data(self):
        return self.get_context().get('search_data', [])

    def get_config_search_data_keys(self):
        return self.get_context().get('search_data_keys', self.get_config_search_data())

    def prepare_search_data(self, obj):
        fields = self.get_config_search_data()
        keys = self.get_config_search_data_keys()
        return self._fields_to_dict(obj, fields, keys)

    def prepare_metadata(self, obj):
        return {}

    def get_model(self):
        return self.get_context().get('model')

    def get_items(self):
        return self.get_model().objects.all()


class BaseGeomIndexMixin(object):
    def get_config_geom_field(self):
        return self.get_context().get('geom_field', 'geom')

    def prepare_geom_field(self, obj):
        return self.get_value(obj, self.get_config_geom_field())

    def prepare_metadata(self, obj):
        return {'srid': 4326, 'geom_type': 'POLYGON'}
