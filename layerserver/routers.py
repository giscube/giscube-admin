# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class DataBaseLayersRouter:
    """
    A router to control all database operations for databaslayers
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read
        """
        if hasattr(model, 'databaselayer_db_connection'):
            return model.databaselayer_db_connection
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write
        """
        if hasattr(model, 'databaselayer_db_connection'):
            return model.databaselayer_db_connection
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return None
