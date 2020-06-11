from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ImageServerConfig(AppConfig):
    name = 'imageserver'
    verbose_name = _('Raster Manager')
