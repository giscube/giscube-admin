from django.dispatch import receiver

from .signals import service_project_updated, service_updated
from .utils import patch_qgis_project, update_external_service


@receiver(service_updated)
def service_updated_handler(sender, obj, **kwargs):
    update_external_service(obj.pk)


@receiver(service_project_updated)
def service_project_updated_handler(sender, obj, **kwargs):
    patch_qgis_project(obj)
