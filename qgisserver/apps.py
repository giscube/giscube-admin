from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QGisServerConfig(AppConfig):
    name = 'qgisserver'
    verbose_name = _('QGIS Projects Manager')

    def ready(self):
        from . import signals  # noqa
