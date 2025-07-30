import os
import tempfile

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail import get_connection
from django.utils import log, timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _
from django.utils.version import get_version as django_get_version


class AdminEmailHandler(log.AdminEmailHandler):
    def send_mail(self, subject, message, *args, **kwargs):
        kwargs['fail_silently'] = False
        mail.mail_admins(subject, message, *args, connection=self.connection(), **kwargs)

    def connection(self):
        return get_connection(backend=self.email_backend, fail_silently=False)


class RecursionException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


def check_recursion(attribute, obj, done=None):
    if done is None:
        done = []
    if obj.pk in done:
        raise RecursionException(_('There is a recursion problem with [%s]') % obj)
    else:
        parent = getattr(obj, attribute)
        if obj.pk and parent and parent.pk:
            done.append(obj.pk)
            check_recursion(attribute, parent, done)


def get_cls(key, default=None):
    value = getattr(settings, key, None)
    if type(value) is type:
        return value
    elif type(value) is tuple or type(value) is list:
        return tuple(import_string(p) for p in value if type(p) is str)
    elif type(value) is str:
        return import_string(value)
    else:
        return default


def get_version(version=None):
    if version is None:
        from giscube import VERSION as version

    return django_get_version(version)


def unique_service_directory(instance, filename=None, append_object_name=True):
    if not instance.service_path:
        path = os.path.join(settings.MEDIA_ROOT, instance._meta.app_label)
        if append_object_name:
            path = os.path.join(path, instance._meta.object_name.lower())
        path = os.path.abspath(path)
        if not os.path.exists(path):
            os.makedirs(path)
        pathname = tempfile.mkdtemp(prefix='%s_' % instance.name, dir=path)
        pathname = os.path.relpath(pathname, settings.MEDIA_ROOT)
        instance.service_path = pathname
    if filename:
        return os.path.join(instance.service_path, filename)
    else:
        return instance.service_path


def clear_tokens_from_old_users(days):
    from oauth2_provider.models import AccessToken, RefreshToken
    User = get_user_model()

    expiring_date = timezone.now() - timedelta(days=days)

    inactive_users = User.objects.filter(
        last_login__lte=expiring_date, is_active=True
    )

    deleted_access = AccessToken.objects.filter(user__in=inactive_users).delete()
    deleted_refresh = RefreshToken.objects.filter(user__in=inactive_users).delete()

    return inactive_users.count(), deleted_access, deleted_refresh


def deactivate_old_users(days):
    User = get_user_model()

    deactivating_date = timezone.now() - timedelta(days=days)

    long_inactive_users = User.objects.filter(
        last_login__lte=deactivating_date, is_active=True
    )

    deactivated_count = long_inactive_users.update(is_active=False, is_staff=False)

    return deactivated_count
