from psycopg2.errors import UndefinedTable

from django.apps import apps
from django.db import connection
from django.db.utils import ProgrammingError

from .models import BaseDocumentIndex


class DocumentIndexEditor(object):
    def __init__(self, name='documentindex'):
        self.app_label = 'giscube_search'
        self.model_name = name.lower()

    def __str__(self):
        return self.model_name

    def make_model(self):
        class Meta:
            app_label = self.app_label
            db_table = 'giscube_search_%s_index' % self.model_name

        attrs = {
            '__module__': self.app_label,
            'Meta': Meta,
        }
        model = type(self.model_name, (BaseDocumentIndex,), attrs)
        return model

    def create(self, model):
        with connection.schema_editor() as editor:
            editor.create_model(model)

    def get_model(self):
        model = self.get_registered_model()

        if model is None:
            model = self.make_model()

            try:
                model.objects.filter(pk=0).exists()
            except ProgrammingError as e:
                if type(e.__cause__) == UndefinedTable:
                    self.create(model)
                else:
                    raise e

            apps.all_models[self.app_label][self.model_name] = model

        return model

    def get_registered_model(self):
        try:
            return apps.get_model(self.app_label, self.model_name)
        except LookupError:
            pass

    def try_unregister_model(self):
        try:
            del apps.all_models[self.app_label][self.model_name]
        except LookupError:
            pass

    def delete(self):
        created_model = self.make_model()
        with connection.schema_editor() as editor:
            try:
                editor.delete_model(created_model)
            except Exception:
                pass
        self.try_unregister_model()
