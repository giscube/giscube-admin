from django.contrib.gis.gdal import OGRGeomType
from django.db.backends.postgresql.introspection import DatabaseIntrospection as OriginalDatabaseIntrospection

from django.contrib.gis.db.backends.postgis.introspection import GeoIntrospectionError
from django.contrib.gis.db.backends.postgis.introspection import PostGISIntrospection as OriginalPostGISIntrospection

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