from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LayerServerConfig(AppConfig):
    name = 'layerserver'
    verbose_name = _('Layer Manager')
