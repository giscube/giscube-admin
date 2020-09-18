from django.contrib.gis.db import models

from giscube.db.utils import get_table_parts

from .model_table_helpers import get_klass, normalize_col_name


class FixDefaultExpression(models.Value):
    def as_sql(self, compiler, connection):
        return self.value, []


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
        field_type, field_params = connection.introspection.get_geometry_type(table_name, row)
        field_notes = []

    return field_type, field_params, field_notes


def _get_fields(connection, cursor, table_name, forced_primary_key_column=None):
    table_parts = get_table_parts(table_name)
    table_name_simple = table_parts['table_name']
    fields = {}

    # TODO: get relations
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

    unique_columns = [
        c['columns'][0] for c in constraints.values()
        if c['unique'] and len(c['columns']) == 1
    ]

    primary_key_column = connection.introspection.get_primary_key_column(cursor, str(table_name_simple))
    if not primary_key_column and forced_primary_key_column:
        primary_key_column = forced_primary_key_column

    table_description = connection.introspection.get_table_description(cursor, table_parts['fixed'])
    used_column_names = []  # Holds column names used in the table so far
    for row in table_description:
        field_type = None
        kwargs = {}

        column_name = row.name
        is_relation = column_name in relations

        name, field_params, field_notes = normalize_col_name(column_name, used_column_names, is_relation)
        kwargs.update(field_params)
        used_column_names.append(name)

        if column_name in unique_columns:
            kwargs['unique'] = True

        if column_name == primary_key_column:
            kwargs['primary_key'] = True
        elif not primary_key_column and column_name == 'id':
            kwargs['primary_key'] = True

        # TODO: Finish relations
        if is_relation and False:
            pass
            # if kwargs.pop('unique', False) or kwargs.get('primary_key'):
            #     field_type = 'OneToOneField'
            # else:
            #     field_type = 'ForeignKey'
            # kwargs['to_field'] = (
            #     "self" if relations[column_name][1] == table_name
            #     else table2model(relations[column_name][1])
            # )
            # kwargs['on_delete'] = models.DO_NOTHING
            # if rel_to in known_models:
            #     field_type = 'ForeignKey(%s' % rel_to
            # else:
            #     field_type = "ForeignKey('%s'" % rel_to
            # field_type = "ForeignKey('%s'" % rel_to
        else:
            # Calling `get_field_type` to get the field type string and any
            # additional parameters and notes.
            field_type, field_params, field_notes = get_field_type(connection, table_name, row)
            kwargs.update(field_params)

            # a Model can only have one AutoField
            if field_type == 'AutoField' and column_name != primary_key_column:
                field_type = 'IntegerField'

        # Add 'null' and 'blank', if the 'null_ok' flag was present in the
        # table description.
        if row.null_ok:
            kwargs['blank'] = True
            kwargs['null'] = True
        else:
            kwargs['blank'] = False
            kwargs['null'] = False

        if row.default is not None and field_type != 'AutoField':
            kwargs['default'] = FixDefaultExpression(row.default)

        fields[name] = {
            'klass': get_klass(field_type),
            'field_type': field_type,
            'kwargs': kwargs
        }

    return fields


def get_fields(connection, table_name, forced_primary_key_column=None):
    with connection.cursor() as cursor:
        fields = _get_fields(connection, cursor, table_name, forced_primary_key_column)
        return fields
