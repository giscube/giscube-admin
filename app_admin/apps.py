from django.apps import AppConfig
from django.utils.translation import gettext_lazy


class AppAdminConfig(AppConfig):
    name = 'app_admin'
    verbose_name = gettext_lazy('Applications administrator and tester')
