from collections import namedtuple

from django.contrib.gis.db.backends.postgis.introspection import PostGISIntrospection as OriginalPostGISIntrospection
from django.contrib.gis.gdal import OGRGeomType
from django.db.backends.base.introspection import FieldInfo as BaseFieldInfo
from django.db.backends.postgresql.introspection import DatabaseIntrospection as OriginalDatabaseIntrospection

from giscube.db.utils import get_table_parts

FieldInfo = namedtuple("FieldInfo", BaseFieldInfo._fields + ("is_autofield",))


class DatabaseIntrospection(OriginalDatabaseIntrospection):
    pass


class PostGISIntrospection(OriginalPostGISIntrospection):
    def get_geometry_type(self, table_name, geo_col):
        """
        The geometry type OID used by PostGIS does not indicate the particular
        type of field that a geometry column is (e.g., whether it's a
        PointField or a PolygonField).  Thus, this routine queries the PostGIS
        metadata tables to determine the geometry type,
        """
        table_parts = get_table_parts(table_name)
        table_name = table_parts['table_name']
        table_schema = table_parts['table_schema']

        cursor = self.connection.cursor()
        try:
            try:
                if table_schema:
                    cursor.execute('SELECT "coord_dimension", "srid", "type" '
                                   'FROM "geometry_columns" '
                                   'WHERE "f_table_name"=%s AND "f_geometry_column"=%s'
                                   'AND "f_table_schema"=%s',
                                   (table_name, geo_col, table_schema))
                else:
                    cursor.execute('SELECT "coord_dimension", "srid", "type" '
                                   'FROM "geometry_columns" '
                                   'WHERE "f_table_name"=%s AND "f_geometry_column"=%s',
                                   (table_name, geo_col))
                row = cursor.fetchone()
                if not row:
                    raise Exception
            except Exception:
                if table_schema:
                    cursor.execute('SELECT "coord_dimension", "srid", "type" '
                                   'FROM "geography_columns" '
                                   'WHERE "f_table_name"=%s AND "f_geometry_column"=%s'
                                   'AND "f_table_schema"=%s',
                                   (table_name, geo_col, table_schema))
                else:
                    cursor.execute('SELECT "coord_dimension", "srid", "type" '
                                   'FROM "geography_columns" '
                                   'WHERE "f_table_name"=%s AND "f_geometry_column"=%s',
                                   (table_name, geo_col))
                row = cursor.fetchone()

            if not row:
                raise Exception('Could not find a geometry or geography column for "%s"."%s"' %
                                (table_name, geo_col))

            # OGRGeomType does not require GDAL and makes it easy to convert
            # from OGC geom type name to Django field.
            field_type = OGRGeomType(row[2]).django

            # Getting any GeometryField keyword arguments that are not the default.
            dim = row[0]
            srid = row[1]
            field_params = {}
            if srid != 4326:
                field_params['srid'] = srid
            if dim != 2:
                field_params['dim'] = dim
        finally:
            cursor.close()

        return field_type, field_params

    def _get_table_description(self, cursor, table_name):
        """
        Return a description of the table with the DB-API cursor.description
        interface.
        """
        table_parts = get_table_parts(table_name)
        table_name = table_parts['table_name']
        table_schema = table_parts['table_schema']

        # Query the pg_catalog tables as cursor.description does not reliably
        # return the nullable property and information_schema.columns does not
        # contain details of materialized views.
        cursor.execute(
            """
            SELECT
                a.attname AS column_name,
                NOT (a.attnotnull OR (t.typtype = 'd' AND t.typnotnull)) AS is_nullable,
                pg_get_expr(ad.adbin, ad.adrelid) AS column_default,
                CASE WHEN collname = 'default' THEN NULL ELSE collname END AS collation,
                a.attidentity != '' AS is_autofield
            FROM pg_attribute a
            LEFT JOIN pg_attrdef ad ON a.attrelid = ad.adrelid AND a.attnum = ad.adnum
            LEFT JOIN pg_collation co ON a.attcollation = co.oid
            JOIN pg_type t ON a.atttypid = t.oid
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE c.relkind IN ('f', 'm', 'p', 'r', 'v')
                AND n.nspname = %s
                AND c.relname = %s
        """,
            [table_schema, table_name],
        )
        field_map = {line[0]: line[1:] for line in cursor.fetchall()}

        sql = "SELECT * FROM %s.%s LIMIT 1" % (
            self.connection.ops.quote_name(table_schema), self.connection.ops.quote_name(table_name),)
        cursor.execute(sql)
        return [
            FieldInfo(
                line.name,
                line.type_code,
                line.display_size,
                line.internal_size,
                line.precision,
                line.scale,
                *field_map[line.name],
            )
            for line in cursor.description
        ]

    def get_table_description(self, cursor, table_name):
        table_parts = get_table_parts(table_name)
        table_schema = table_parts['table_schema']
        if table_schema:
            return self._get_table_description(cursor, table_name)
        else:
            return super().get_table_description(cursor, table_name)

    def _get_current_user(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT current_user;')
        return cursor.fetchone()[0]

    def join_schema_table_name(self, table_schema, table_name):
        return '"%s"."%s"' % (table_schema, table_name)

    def get_fixed_table_name(self, table_name):
        table_parts = get_table_parts(table_name)
        table_name = table_parts['table_name']
        table_schema = table_parts['table_schema']

        if table_schema:
            return table_parts['fixed']

        self._get_current_user()
        sql = "SHOW search_path;"
        cursor = self.connection.cursor()
        cursor.execute(sql)
        search_path = cursor.fetchone()
        for schema in search_path[0].split(','):
            schema = schema.strip()
            if schema == '"$user"':
                schema = self._get_current_user()
            if self.table_exists(schema, table_name):
                return self.join_schema_table_name(schema, table_name)

    def table_exists(self, table_schema, table_name):
        cursor = self.connection.cursor()
        try:
            sql = "SELECT * FROM %s.%s LIMIT 1" % (
                self.connection.ops.quote_name(table_schema), self.connection.ops.quote_name(table_name),)
            cursor.execute(sql)
        except Exception:
            return False
        return True
