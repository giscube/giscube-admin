from django.apps import apps
from django.db import models
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.functional import cached_property

from giscube.db.utils import get_table_parts

from ..widgets import widgets_types
from .model_table import get_fields
from .model_table_helpers import random_string
from .sql_compiler_patch import PostgresCompilerManager


models_module = None


class FilterDataManager(PostgresCompilerManager):
    def __init__(self, *args, **kwargs):
        self.data_filter = kwargs.pop('data_filter')
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.data_filter:
            qs = qs.filter(**self.data_filter)
        return qs


class ModelFactory:
    app_label = 'layerserver_databaselayer'

    def __init__(self, layer, exclude_enabled=True):
        self.layer = layer
        self.table_parts = get_table_parts(layer.table)
        self.unique_tag = ''
        self.conn = None
        self.exclude_enabled = exclude_enabled

    def __enter__(self):
        self.unique_tag = random_string()
        return self.get_model()

    def __exit__(self, *args, **kwargs):
        self.try_unregister_model()

    def set_conn(self):
        self.layer.db_connection.get_connection(schema=self.table_parts['table_schema'])
        self.conn = self.layer.db_connection.connection_name(schema=self.table_parts['table_schema'])

    def get_model(self):
        return self.get_registered_model() or self.make_model()

    def get_registered_model(self):
        try:
            return apps.get_model(self.app_label, self.model_name)
        except LookupError:
            pass

    def try_unregister_model(self):
        try:
            del apps.all_models[self.app_label][self.model_name.lower()]
        except LookupError:
            pass

    def make_model(self):
        self.try_unregister_model()
        self.set_conn()
        model = type(
            self.model_name,
            (models.Model,),
            {**self.fields, **self.base_attributes}
        )
        return model

    # @cached_property
    @property
    def base_attributes(self):
        return {
            '__module__': 'layerserver_databaselayer.models',
            '_declared': timezone.now(),
            '_giscube_dblayer_schema': self._get_schema(),
            '_giscube_dblayer_db_connection': self.conn,
            'objects': FilterDataManager(data_filter=self.layer.data_filter),
            'objects_default': models.Manager(),
            'Meta': self.model_meta,
        }

    # @cached_property
    @property
    def model_meta(self):
        class Meta:
            app_label = self.app_label
            db_table = self.layer.table
            verbose_name = self.layer.name
            ordering = [self.layer.pk_field]
            managed = False
        return Meta

    @cached_property
    def original_fields(self):
        table_name = self.table_parts['fixed']
        table_schema = self.table_parts['table_schema']
        conn = self.layer.db_connection.get_connection(schema=table_schema)
        return get_fields(conn, table_name, self.layer.pk_field)

    @cached_property
    def fields(self):
        model_fields = {}
        for field_options in self.field_options:
            widget = widgets_types[field_options.widget]
            field = self.original_fields[field_options.name]
            options = {
                'blank': field_options.blank
            }
            if not field_options.enabled or field_options.readonly:
                options['editable'] = False
            field['kwargs'].update(options)
            if self.layer.geom_field and self.layer.geom_field == field_options.name:
                field['kwargs'].update({'srid': self.layer.srid})
            model_fields[field_options.name] = widget.apply(field, field_options, {'layer': self.layer})
            model_fields[field_options.name]._giscube_field = model_to_dict(field_options)
        return model_fields

    @property
    def field_options(self):
        return self.layer.fields.all()

    @property
    def model_name(self):
        name = self.layer.table.replace(
            '"."', '-').replace('"', '').replace('.', ' ').title().replace(' ', '').replace('_', '').replace('-', '_')
        return '%s%s' % (name, self.unique_tag)

    def _get_schema(self):
        return {
            'name': self.layer.name,
            'table': self.layer.table,
            'pk_field': self.layer.pk_field,
            'geom_field': self.layer.geom_field,
            'srid': self.layer.srid
        }
