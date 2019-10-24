import json
import os
import random
import re
import string
from collections import OrderedDict

from django.apps import apps
from django.conf import settings
from django.contrib.gis.db import models
from django.core.management.commands.inspectdb import Command
from django.utils import timezone
from django.utils.functional import cached_property

from giscube.db.utils import get_table_parts

from .fields import ImageWithThumbnailField
from .storage import get_image_with_thumbnail_storage_class


def get_field_type(connection, table_name, row):
    """
    Given the database connection, the table name, and the cursor row
    description, this routine will return the given field type name, as
    well as any additional keyword parameters and notes for the field.
    """
    field_params = {}
    field_notes = []

    try:
        field_type = connection.introspection.get_field_type(row.type_code, row)
    except KeyError:
        field_type = 'TextField'
        field_notes.append('This field type is a guess.')

    # Add max_length for all CharFields.
    if field_type == 'CharField' and row.internal_size:
        field_params['max_length'] = int(row.internal_size)

    if field_type == 'DecimalField':
        if row.precision is None or row.scale is None:
            field_notes.append(
                'max_digits and decimal_places have been guessed, as this '
                'database handles decimal fields as float')
            field_params['max_digits'] = row.precision if row.precision is not None else 10
            field_params['decimal_places'] = row.scale if row.scale is not None else 5
        else:
            field_params['max_digits'] = row.precision
            field_params['decimal_places'] = row.scale

    if field_type == 'GeometryField':
        field_type, field_params = connection.introspection.get_geometry_type(table_name, row[0])
        field_notes = []

    return field_type, field_params, field_notes


def table2model(table_name):
    return re.sub(r'[^a-zA-Z0-9]', '', table_name.title())


def strip_prefix(s):
    return s[1:] if s.startswith("u'") else s


def get_fields(connection, table_name):
    table_parts = get_table_parts(table_name)
    table_name_simple = table_parts['table_name']
    fields = {}
    cursor = connection.cursor()

    relations = {}
    # try:
    #     indexes = connection.introspection.get_indexes(cursor, table_name_simple)
    # except NotImplementedError:
    #     indexes = {}
    constraints = {}
    try:
        constraints = connection.introspection.get_constraints(cursor, table_name_simple)
    except NotImplementedError:
        pass

    primary_key_column = connection.introspection.get_primary_key_column(cursor, str(table_name_simple))
    unique_columns = [
        c['columns'][0] for c in constraints.values()
        if c['unique'] and len(c['columns']) == 1
    ]
    table_description = connection.introspection.get_table_description(cursor, table_name)
    used_column_names = []  # Holds column names used in the table so far
    column_to_field_name = {}  # Maps column names to names of model fields
    # for row in get_table_description(cursor, unicode(table_name_simple)):
    for row in table_description:
        comment_notes = []  # Holds Field notes, to be displayed in a Python comment.
        extra_params = OrderedDict()  # Holds Field parameters such as 'db_column'.
        column_name = row[0]
        is_relation = column_name in relations

        att_name, params, notes = Command.normalize_col_name(Command, column_name, used_column_names, is_relation)
        extra_params.update(params)
        comment_notes.extend(notes)

        used_column_names.append(att_name)
        column_to_field_name[column_name] = att_name

        # Add primary_key and unique, if necessary.
        if column_name == primary_key_column:
            extra_params['primary_key'] = True
        elif column_name in unique_columns:
            extra_params['unique'] = True

        if is_relation:
            rel_to = (
                "self" if relations[column_name][1] == table_name
                else table2model(relations[column_name][1])
            )
            # if rel_to in known_models:
            #     field_type = 'ForeignKey(%s' % rel_to
            # else:
            #     field_type = "ForeignKey('%s'" % rel_to
            field_type = "ForeignKey('%s'" % rel_to
        else:
            # Calling `get_field_type` to get the field type string and any
            # additional parameters and notes.
            field_type, field_params, field_notes = get_field_type(connection, table_name, row)
            extra_params.update(field_params)
            comment_notes.extend(field_notes)

            # a Model can only have one AutoField
            if field_type == 'AutoField' and att_name != primary_key_column:
                field_type = 'IntegerField'

            field_type += '('

        # Don't output 'id = meta.AutoField(primary_key=True)', because
        # that's assumed if it doesn't exist.
        if att_name == 'id' and extra_params == {'primary_key': True}:
            if field_type == 'AutoField(':
                # continue
                pass
            elif field_type == 'IntegerField(' and not connection.features.can_introspect_autofield:
                comment_notes.append('AutoField?')

        # Add 'null' and 'blank', if the 'null_ok' flag was present in the
        # table description.
        if row[6]:  # If it's NULL...
            if field_type == 'BooleanField(':
                field_type = 'NullBooleanField('
            else:
                extra_params['blank'] = True
                extra_params['null'] = True

        # field_desc = '%s = %s%s' % (
        #    att_name,
        field_desc = '%s%s' % (
            # Custom fields will have a dotted path
            '' if '.' in field_type else 'models.',
            field_type,
        )
        if field_type.startswith('ForeignKey('):
            field_desc += ', models.DO_NOTHING'

        if extra_params:
            if not field_desc.endswith('('):
                field_desc += ', '
            field_desc += ', '.join(
                '%s=%s' % (k, strip_prefix(repr(v)))
                for k, v in list(extra_params.items()))
        field_desc += ')'
        # if comment_notes:
        #     field_desc += '  # ' + ' '.join(comment_notes)
        # yield '    %s' % field_desc
        fields[att_name] = eval('    %s' % field_desc)

    # for meta_line in self.get_meta(table_name, constraints, column_to_field_name):
    #     yield meta_line
    return fields


def create_dblayer_model(layer):
    return ModelFactory(layer).get_model()


class ModelFactory:
    def __init__(self, layer):
        self.layer = layer
        self.app_label = 'layerserver_databaselayer'
        self.unique_tag = ''

    def __exit__(self, *args, **kwargs):
        self.destroy()

    def __enter__(self):
        self.unique_tag = self._random_string()
        return self.get_model()

    @cached_property
    def get_layer_fields(self):
        return self.layer.fields.all()

    def apply_blank(self, fields):
        for field in self.get_layer_fields:
            if getattr(fields[field.name], 'blank') != field.blank:
                setattr(fields[field.name], 'blank', field.blank)

    def apply_widgets(self, fields):
        from .models import DataBaseLayerField
        for field in self.get_layer_fields:
            if field.widget == DataBaseLayerField.WIDGET_CHOICES.image:
                try:
                    fields[field.name] = self.to_image_field(field, fields[field.name])
                except Exception:
                    raise Exception('Invalid configuration for field [%s]' % field.name)

    def destroy(self):
        last_model = self.get_registered_model()
        if last_model:
            self.try_unregister_model()

    def get_attributes(self):
        attrs = {}
        attrs.update(self._base_attributes())
        attrs.update(self._custom_fields())
        return attrs

    @property
    def model_name(self):
        name = self.layer.table.replace(
            '"."', '-').replace('"', '').replace('.', ' ').title().replace(' ', '').replace('_', '').replace('-', '_')
        return '%s%s' % (name, self.unique_tag)

    def get_model(self):
        return self.get_registered_model() or self.make()

    def get_registered_model(self):
        model = None
        try:
            model = apps.get_model(self.app_label, self.model_name)
        except LookupError:
            pass
        return model

    def make(self):
        self.try_unregister_model()
        model = type(
            self.model_name,
            (models.Model,),
            self.get_attributes()
        )
        return model

    def get_auto_images_root(self, layer, field_name):
        return os.path.join(settings.MEDIA_ROOT, layer.service_path, 'field_%s' % field_name, 'images')

    def get_auto_thumbnails_root(self, layer, field_name):
        return os.path.join(settings.MEDIA_ROOT, layer.service_path, 'field_%s' % field_name, 'images')

    def _random_string(self, string_length=24):
        letters_digits = string.ascii_letters + string.digits
        return ''.join(random.choice(letters_digits) for i in range(string_length))

    def _get_storage_class(self, field, widget_options):
        """
        'upload_root' must contains the full folder path to avoid folders in the image name.
        That's why upload_to is not used.
        """
        if 'upload_root' in widget_options:
            upload_root = widget_options['upload_root']
            base_url = widget_options.get('base_url', None)
            thumbnail_root = widget_options.get('thumbnail_root', None)
            thumbnail_base_url = widget_options.get('thumbnail_base_url', None)
            if upload_root == '<auto>':
                upload_root = self.get_auto_images_root(field.layer, field.name)
                base_url = None
            if thumbnail_root == '<auto>':
                thumbnail_root = self.get_auto_thumbnails_root(field.layer, field.name)
                thumbnail_base_url = None
            StorageClass = get_image_with_thumbnail_storage_class()
            storage = StorageClass(
                location=upload_root,
                base_url=base_url,
                thumbnail_location=thumbnail_root,
                thumbnail_base_url=thumbnail_base_url,
                thumbnail_width=widget_options.get('thumbnail_width', None),
                thumbnail_height=widget_options.get('thumbnail_height', None)
            )
            storage.save_thumbnail_enabled = thumbnail_root is not None
            return storage

    def to_image_field(self, field, original_field):
        widget_options = json.loads(field.widget_options)
        options = {
            'validators': [],
            'blank': original_field.blank,
            'null': original_field.null,
            'db_index': original_field.db_index,
            'primary_key': original_field.db_index,
            'name': original_field.name or field.name,
            'db_tablespace': original_field.db_tablespace,
            'db_column': original_field.db_column or field.name,
            'default': original_field.default,
            'editable': original_field.editable,
            'max_length': original_field.max_length,
            'widget_options': widget_options,
            'storage': self._get_storage_class(field, widget_options)
        }
        f = ImageWithThumbnailField(**options)
        return f

    def try_unregister_model(self):
        try:
            del apps.all_models[self.app_label][self.model_name.lower()]
        except LookupError:
            pass

    def _base_attributes(self):
        table_parts = get_table_parts(self.layer.table)
        return {
            '__module__': 'layerserver_databaselayer.models',
            '_declared': timezone.now(),
            '_schema': self._get_schema(),
            'databaselayer_db_connection': self.layer.db_connection.connection_name(
                schema=table_parts['table_schema']),
            'Meta': self._model_meta(),
        }

    def _custom_fields(self):
        table_parts = get_table_parts(self.layer.table)
        table_schema = table_parts['table_schema']
        table = table_parts['fixed']

        fields = get_fields(self.layer.db_connection.get_connection(schema=table_schema), table)

        # Add primary_key if needed
        primary_key = None
        for fied_name, field in list(fields.items()):
            if getattr(field, 'primary_key'):
                primary_key = fied_name
                break
        if primary_key is None:
            setattr(fields[self.layer.pk_field], 'primary_key', True)

        self.apply_blank(fields)
        self.apply_widgets(fields)
        if self.layer.geom_field:
            fields[self.layer.geom_field].srid = self.layer.srid

        return fields

    def _model_meta(self):
        class Meta:
            app_label = self.app_label
            db_table = self.layer.table
            verbose_name = self.layer.name
            ordering = [self.layer.pk_field]
            managed = False
        return Meta

    def _get_schema(self):
        return {
            'name': self.layer.name,
            'table': self.layer.table,
            'pk_field': self.layer.pk_field,
            'geom_field': self.layer.geom_field,
            'srid': self.layer.srid
        }
