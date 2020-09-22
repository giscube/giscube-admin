from django.utils.translation import ugettext_lazy as _

from django_celery_results.apps import CeleryResultConfig
from oauth2_provider.apps import DOTConfig


class GiscubeOauth2ProviderConfig(DOTConfig):
    verbose_name = _('Security')


class GiscubeCeleryResultConfig(CeleryResultConfig):
    verbose_name = _('Internal Processes Results')
