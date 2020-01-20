class DataBaseLayersRouter:
    """
    A router to control all database operations for databaslayers
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read
        """
        if hasattr(model, '_giscube_dblayer_db_connection'):
            return model._giscube_dblayer_db_connection

    def db_for_write(self, model, **hints):
        """
        Attempts to write
        """
        if hasattr(model, '_giscube_dblayer_db_connection'):
            return model._giscube_dblayer_db_connection

    def allow_relation(self, obj1, obj2, **hints):
        pass

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        pass
