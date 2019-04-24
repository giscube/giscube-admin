import json
import re
from collections import OrderedDict

from django.conf import settings
from django.contrib.gis.db import models
from django.core.management.commands.inspectdb import Command

from giscube.db.utils import get_table_parts
from .storage import get_thumbnail_storage_klass


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

            field_type += '('

        # Don't output 'id = meta.AutoField(primary_key=True)', because
        # that's assumed if it doesn't exist.
        if att_name == 'id' and extra_params == {'primary_key': True}:
            if field_type == 'AutoField(':
                #continue
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

        #field_desc = '%s = %s%s' % (
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


class ImageWithThumbnailField(models.FileField):
    widget_options = None

    def __init__(self, *args, **kwargs):
        self.widget_options = kwargs.pop('widget_options')
        StorageKlass = get_thumbnail_storage_klass()
        storage = StorageKlass(
            location=self.widget_options['upload_root'],
            base_url=self.widget_options.get('base_url', None),
            thumbnail_location=self.widget_options.get('thumbnail_root', None),
            thumbnail_base_url=self.widget_options.get('thumbnail_base_url', None),
            thumbnail_width=self.widget_options.get('thumbnail_width', settings.LAYERSERVER_THUMBNAIL_WIDTH),
            thumbnail_height=self.widget_options.get('thumbnail_height', settings.LAYERSERVER_THUMBNAIL_HEIGHT)
        )
        kwargs['storage'] = storage
        super().__init__(*args, **kwargs)
        self.validators = []


def to_image_field(field, original_field):
    options = {
        'validators': [],
        'blank': original_field.blank,
        'null': original_field.null,
        'db_index': original_field.db_index,
        'primary_key': original_field.db_index,
        'name': original_field.name,
        'db_tablespace': original_field.db_tablespace,
        'db_column': original_field.db_column,
        'default': original_field.default,
        'editable': original_field.editable,
        'max_length': original_field.max_length,
        'widget_options': json.loads(field.widget_options)
    }
    return ImageWithThumbnailField(**options)


def apply_blank(layer, fields):
    for field in layer.fields.all():
        if getattr(fields[field.name], 'blank') != field.blank:
            setattr(fields[field.name], 'blank', field.blank)


def apply_widgets(layer, fields):
    from .models import DataBaseLayerField
    for field in layer.fields.all():
        if field.widget == DataBaseLayerField.WIDGET_CHOICES.image:
            try:
                fields[field.name] = to_image_field(field, fields[field.name])
            except Exception:
                raise Exception('Invalid configuration for field [%s]' % field.name)


def create_dblayer_model(layer):
    table_parts = get_table_parts(layer.table)
    table_schema = table_parts['table_schema']
    table = table_parts['fixed']

    class Meta:
        app_label = 'layerserver_databaselayer'
        db_table = layer.table
        verbose_name = layer.name
        ordering = [layer.pk_field]
        managed = False

    @staticmethod
    def get_layer():
        return layer

    attrs = {
        '__module__': 'layerserver_databaselayer',
        'Meta': Meta,
        'get_layer': get_layer,
        'databaselayer_db_connection': layer.db_connection.connection_name(
            schema=table_schema)
    }
    fields = get_fields(layer.db_connection.get_connection(schema=table_schema), table)

    # Add primary_key if needed
    primary_key = None
    for fied_name, field in list(fields.items()):
        if getattr(field, 'primary_key'):
            primary_key = fied_name
            break
    if primary_key is None:
        setattr(fields[layer.pk_field], 'primary_key', True)

    apply_blank(layer, fields)
    apply_widgets(layer, fields)
    if layer.geom_field:
        fields[layer.geom_field].srid = layer.srid
    attrs.update(fields)
    model_name = layer.table.replace('".""', ' ').replace('"', '').replace('.', ' ').title().replace(' ', '')
    model = type(str(model_name), (models.Model,), attrs)

    return model
