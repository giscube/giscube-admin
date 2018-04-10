import os

from django.db import models
from django.dispatch import receiver

from qgisserver.utils import unique_service_directory
from qgisserver.utils import patch_qgis_project

SERVICE_VISIBILITY_CHOICES = [
    ('private', 'Private'),
    ('public', 'Public'),
]


class Service(models.Model):
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    keywords = models.CharField(max_length=200, null=True, blank=True)
    project_file = models.FileField(upload_to=unique_service_directory)
    service_path = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    visibility = models.CharField(max_length=10, default='private',
                                  choices=SERVICE_VISIBILITY_CHOICES)
    visible_on_geoportal = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super(Service, self).save(*args, **kwargs)
        patch_qgis_project(self)

    def __unicode__(self):
        return unicode(self.title or self.name)


@receiver(models.signals.post_delete, sender=Service)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Delete the project file if the service is deleted
    """
    if instance.project_file:
        if os.path.isfile(instance.project_file.path):
            os.remove(instance.project_file.path)


@receiver(models.signals.pre_save, sender=Service)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Delete the project file only when it changes
    """
    if not instance.pk:
        return False

    try:
        old_file = Service.objects.get(pk=instance.pk).project_file
    except Service.DoesNotExist:
        return False

    new_file = instance.project_file
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


class Project(models.Model):
    name = models.CharField(max_length=50)
    data = models.TextField()
    service = models.ForeignKey(Service, null=True, blank=True,
                                on_delete=models.SET_NULL)
