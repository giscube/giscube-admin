from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class GiscubeConfig(AppConfig):
    name = 'giscube'
    label = 'giscube'
    verbose_name = _('General Settings')
