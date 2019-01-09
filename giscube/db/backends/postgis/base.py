from django.db.backends.base.base import NO_DB_ALIAS

from django.contrib.gis.db.backends.postgis.features import DatabaseFeatures
from .introspection import PostGISIntrospection
from django.contrib.gis.db.backends.postgis.operations import PostGISOperations
from django.contrib.gis.db.backends.postgis.schema import PostGISSchemaEditor
from django.contrib.gis.db.backends.postgis.base import DatabaseWrapper as OriginalDatabaseWrapper


class DatabaseWrapper(OriginalDatabaseWrapper):
    SchemaEditorClass = PostGISSchemaEditor

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)
        if kwargs.get('alias', '') != NO_DB_ALIAS:
            self.features = DatabaseFeatures(self)
            self.ops = PostGISOperations(self)
            self.introspection = PostGISIntrospection(self)
