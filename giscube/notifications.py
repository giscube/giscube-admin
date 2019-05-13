from django.conf import settings
from django.core.mail import mail_admins


def notify_deprecated(msg):
    message = 'APP_URL: %s\n\n%s' % (settings.APP_URL, msg)
    mail_admins('DEPRECATED', message, fail_silently=True)
