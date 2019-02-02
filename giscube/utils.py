import os
import tempfile

from django.conf import settings
from django.utils.version import get_version as django_get_version


def get_version(version=None):
    if version is None:
        from . import VERSION as version

    return django_get_version(version)


def unique_service_directory(instance, filename=None):
    if not instance.service_path:
        path = os.path.join(settings.MEDIA_ROOT, instance._meta.app_label)
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
