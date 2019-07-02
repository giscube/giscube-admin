from django.conf import settings
from django.core.mail import mail_admins


def notify_deprecated(msg, request=None):
    message_parts = []
    if request is None:
        message_parts.append('APP_URL: %s' % settings.APP_URL)
    else:
        message_parts.append('URL: %s' % request.build_absolute_uri())
    message_parts.append(msg)
    message = '\n\n'.join(message_parts)
    mail_admins('DEPRECATED', message, fail_silently=True)
