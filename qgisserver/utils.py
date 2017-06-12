import os
import tempfile
import xml.etree.ElementTree as ET

from django.conf import settings


def patch_qgis_project(service):
    filename = service.project.path
    tree = ET.parse(filename)
    root = tree.getroot()
    properties = root.find('properties')
    wms_url = properties.find('WMSUrl')
    if wms_url is None:
        wms_url = ET.SubElement(properties, 'WMSUrl')
    giscube_url = getattr(settings, 'GISCUBE_URL', 'http://localhost:8080')
    wms_url.text = '%s/qgisserver/services/%s/' % (giscube_url, service.name)
    tree.write(filename)


def unique_service_directory(instance, filename):
    if not instance.service_path:
        path = os.path.join(settings.MEDIA_ROOT, instance._meta.app_label)
        path = os.path.abspath(path)
        if not os.path.exists(path):
            os.makedirs(path)
        pathname = tempfile.mkdtemp(prefix='%s_' % instance.name, dir=path)
        pathname = os.path.relpath(pathname, settings.MEDIA_ROOT)
        instance.service_path = pathname
    return os.path.join(instance.service_path, filename)
