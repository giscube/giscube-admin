from django.contrib.gis.db.backends.postgis.introspection import GeoIntrospectionError
from django.contrib.gis.db.backends.postgis.introspection import PostGISIntrospection as OriginalPostGISIntrospection
from django.contrib.gis.gdal import OGRGeomType
from django.db.backends.postgresql.introspection import DatabaseIntrospection as OriginalDatabaseIntrospection
from django.db.backends.postgresql.introspection import FieldInfo

from giscube.db.utils import get_table_parts


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
                    raise GeoIntrospectionError
            except GeoIntrospectionError:
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

    def get_table_description(self, cursor, table_name):
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
        cursor.execute("""
            SELECT
                a.attname AS column_name,
                NOT (a.attnotnull OR (t.typtype = 'd' AND t.typnotnull)) AS is_nullable,
                pg_get_expr(ad.adbin, ad.adrelid) AS column_default
            FROM pg_attribute a
            LEFT JOIN pg_attrdef ad ON a.attrelid = ad.adrelid AND a.attnum = ad.adnum
            JOIN pg_type t ON a.atttypid = t.oid
            JOIN pg_class c ON a.attrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE c.relkind IN ('f', 'm', 'p', 'r', 'v')
                AND c.relname = %s
                AND n.nspname NOT IN ('pg_catalog', 'pg_toast')
                AND pg_catalog.pg_table_is_visible(c.oid)
        """, [table_name])
        field_map = {line[0]: line[1:] for line in cursor.fetchall()}
        if table_schema:
            sql = "SELECT * FROM %s.%s LIMIT 1" % (
                self.connection.ops.quote_name(table_schema), self.connection.ops.quote_name(table_name),)
        else:
            sql = "SELECT * FROM %s LIMIT 1" % self.connection.ops.quote_name(table_name)
        cursor.execute(sql)
        return [
            FieldInfo(
                line.name,
                line.type_code,
                line.display_size,
                line.internal_size,
                line.precision,
                line.scale,
                *field_map[line.name]
            )
            for line in cursor.description
        ]
