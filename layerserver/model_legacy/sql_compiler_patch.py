from sql_compiler.compilers.postgresql import PostgresCompiler

from django.db import connections
from django.db.models import Manager, QuerySet
from django.utils.functional import cached_property


class SQLCompilerQuerySet(QuerySet):

    @cached_property
    def executable_query(self):
        connection = connections[self.db]
        query, params = self.query.sql_with_params()
        compiler = PostgresCompiler()
        return compiler.compile_sql(connection, query, params)


class PostgresCompilerManager(Manager):

    def get_queryset(self):
        return SQLCompilerQuerySet(self.model, using=self._db)
