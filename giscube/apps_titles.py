from django.utils.translation import ugettext_lazy as _

from oauth2_provider.apps import DOTConfig
from django_celery_results.apps import CeleryResultConfig


class GiscubeOauth2ProviderConfig(DOTConfig):
    verbose_name = _('Security')


class GiscubeCeleryResultConfig(CeleryResultConfig):
    verbose_name = _('Internal Processes Results')
