import glob
import os
import tempfile

from django.conf import settings


def unique_service_directory(instance):
    path = os.path.join(settings.VAR_ROOT, instance._meta.app_label)
    path = os.path.abspath(path)
    if not os.path.exists(path):
        os.makedirs(path)
    pathname = tempfile.mkdtemp(prefix='%s_' % instance.name, dir=path)
    return pathname


def unique_layer_directory(instance):
    path = os.path.join(settings.VAR_ROOT, instance._meta.app_label)
    path = os.path.abspath(path)
    if not os.path.exists(path):
        os.makedirs(path)
    pathname = tempfile.mkdtemp(prefix='%s_' % instance.name, dir=path)
    media_root = os.path.abspath(settings.VAR_ROOT)
    if media_root == pathname[:len(media_root)]:
        return pathname[len(media_root) + 1:]
    else:
        raise Exception("Error while getting layer path")


def find_shapefile(dir):
    if dir is None:
        raise Exception("Invalid directory")
    shapes = glob.glob('%s/*.shp' % dir)
    return shapes[0]
