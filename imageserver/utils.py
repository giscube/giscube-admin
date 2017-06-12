import glob
import os
import shutil
import tempfile
import zipfile

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


def extract_zipfile(name, subdir='files'):
    if os.path.isfile(name) and zipfile.is_zipfile(name):
        zf = zipfile.ZipFile(name, 'r')
        target_path = os.path.join(os.path.dirname(name), subdir)
        # clean directory
        abs_path = os.path.abspath(target_path)
        if os.path.exists(abs_path):
            shutil.rmtree(abs_path)
        os.makedirs(abs_path)
        zf.extractall(abs_path)
        return abs_path


def find_shapefile(dir):
    if dir is None:
        raise Exception("Invalid directory")
    shapes = glob.glob('%s/*.shp' % dir)
    return shapes[0]
