from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GiscubeConfig(AppConfig):
    name = 'giscube'
    label = 'giscube'
    verbose_name = _('General Settings')
