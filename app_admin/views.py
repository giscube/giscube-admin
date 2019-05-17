from django.conf import settings
from django.core.mail import mail_admins
from django.http import HttpResponse
from django.template.response import SimpleTemplateResponse
from django.utils.translation import gettext as _
from django.views import View


class AppAdminView(View):
    http_method_names = ['get', 'options']
    show_settings = [
        'ADMINS',
        'SITE_URL',
        'EMAIL_BACKEND',
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_HOST_USER',
        'DEFAULT_FROM_EMAIL',
    ]

    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_superuser:
            return HttpResponse(status=404)
        return super().dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        action = self.request.GET.get('action', None)

        if action == 'crash':
            raise Exception('Forced crash to test some part of the code or configuration')
        elif action == 'mail_admins':
            mail_admins('[django app admin] mail_admins', _('Email sent from mail_admins of app_admin'))
            return HttpResponse('mail_admins OK')
        else:
            s = {key: getattr(settings, key, None) for key in self.show_settings}
            return SimpleTemplateResponse('app_admin.html', {'settings': s})
