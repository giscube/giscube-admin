import os

from django.core.exceptions import ValidationError
from django.core.validators import validate_comma_separated_integer_list
from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext as _

from giscube.models import Category, Server
from qgisserver.utils import patch_qgis_project, unique_service_directory

SERVICE_VISIBILITY_CHOICES = [
    ('private', 'Private'),
    ('public', 'Public'),
]


def validate_integer_pair(value):
    values = []
    try:
        values = map(int, value.split(','))
    except:
        pass

    if len(values) == 2:
        if not value == ('%s,%s' % tuple(values)):
            raise ValidationError(
                _('Enter only digits separated by commas.'),
            )

    else:
        raise ValidationError(
            _('%(value)s must be a pair of integer, e.g. 12,12'),
            params={'value': value},
        )


def validate_integer_pair_list(value):
    for line in value.splitlines():
        validate_integer_pair(line)


class Service(models.Model):
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='qgisserver_services')
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
    wms_buffer_enabled = models.BooleanField(
        _('buffer enabled'), default=False
    )
    wms_buffer_size = models.CharField(
        _('buffer size'), max_length=12, null=True, blank=True,
        help_text='Buffer around tiles, e.g. 64,64',
        validators=[validate_integer_pair]
    )
    wms_tile_sizes = models.TextField(
        _('tile sizes'), null=True, blank=True,
        help_text='Integer pairs in different lines e.g.<br/>256,256<br/>512,512',
        validators=[validate_integer_pair_list]
    )
    servers = models.ManyToManyField(Server, blank=True)

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
    data = models.TextField(null=True, blank=True)
    service = models.ForeignKey(Service, null=True, blank=True,
                                on_delete=models.SET_NULL)
