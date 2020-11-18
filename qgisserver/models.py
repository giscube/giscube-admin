import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext as _

from giscube.model_mixins import MetadataModelMixin, ResourceModelMixin
from giscube.models import Category, Server
from giscube.tilecache.models_mixins import TileCacheModelMixin
from giscube.validators import validate_options_json_format
from qgisserver.utils import (deactivate_services, patch_qgis_project, unique_service_directory,
                              update_external_service, url_slash_join)


SERVICE_VISIBILITY_CHOICES = [
    ('private', _('Private')),
    ('public', _('Public')),
]


def validate_integer_pair(value):
    values = []
    try:
        values = list(map(int, value.split(',')))
    except Exception:
        pass

    if len(values) == 2:
        if not value == ('%s,%s' % tuple(values)):
            raise ValidationError(_('Enter only digits separated by commas.'))

    else:
        raise ValidationError(_('%s must be a pair of integer, e.g. 12,12') % value)


def validate_integer_pair_list(value):
    for line in value.splitlines():
        validate_integer_pair(line)


class Service(TileCacheModelMixin, models.Model):
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='qgisserver_services')
    name = models.CharField(_('name'), max_length=50, unique=True)
    title = models.CharField(_('title'), max_length=100, null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)
    keywords = models.CharField(_('keywords'), max_length=200, null=True, blank=True)
    project_file = models.FileField(_('project file'), upload_to=unique_service_directory)
    service_path = models.CharField(_('service path'), max_length=255)
    active = models.BooleanField(_('active'), default=True, help_text='Enable/disable usage')
    visibility = models.CharField(_('visibility'), max_length=10, default='private',
                                  help_text='visibility=\'Private\' restricts usage to authenticated users',
                                  choices=SERVICE_VISIBILITY_CHOICES)
    visible_on_geoportal = models.BooleanField(_('visible on geoportal'), default=False)
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
    options = models.TextField(_('options'), null=True, blank=True, help_text='json format. Ex: {"maxZoom": 20}',
                               validators=[validate_options_json_format])
    legend = models.TextField(_('legend'), null=True, blank=True)

    @property
    def default_layer(self):
        if self.project_file:
            project_file = os.path.basename(self.project_file.url)
            filename, _ = os.path.splitext(project_file)
            return filename

    @property
    def service_url(self):
        return url_slash_join(settings.GISCUBE_URL, '/qgisserver/services/%s' % self.name)

    @property
    def service_internal_url(self):
        server_url = settings.GISCUBE_QGIS_SERVER_URL
        mapfile = "map=%s" % self.project_file.path
        if '?' not in server_url:
            server_url = '%s?' % server_url
        if not server_url.endswith('?'):
            server_url = '%s&' % server_url
        url = "%s%s" % (server_url, mapfile)
        return url

    def save(self, *args, **kwargs):
        super(Service, self).save(*args, **kwargs)
        patch_qgis_project(self)
        update_external_service.delay(self.pk)

    def __str__(self):
        return str(self.title or self.name)

    @property
    def anonymous_view(self):
        return not (self.visibility == 'private')

    class Meta:
        verbose_name = _('Service')
        verbose_name_plural = _('Services')


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


@receiver(models.signals.m2m_changed, sender=Service.servers.through)
def service_active_auto_control(sender, **kwargs):
    """
    Request the server which no longer has the service to deactivate it
    """
    instance = kwargs.pop('instance', None)
    action = kwargs.pop('action', None)

    if action == 'post_add' or action == 'post_remove' or action == 'post_clear':
        instance.active = Server.objects.filter(service=instance, this_server=True).exists()
        instance.save()


@receiver(models.signals.m2m_changed, sender=Service.servers.through)
def auto_dectivate_external_services(sender, **kwargs):
    """
    Request the server which no longer has the service to deactivate it
    """
    instance = kwargs.pop('instance', None)
    pk_set = kwargs.pop('pk_set', None)
    action = kwargs.pop('action', None)

    if action == 'post_remove' or action == 'post_clear':
        deactivate_services.delay(instance.name, list(pk_set))


class ServiceMetadata(MetadataModelMixin):
    parent = models.OneToOneField(Service, on_delete=models.CASCADE, primary_key=True, related_name='metadata')


class ServiceResource(ResourceModelMixin):
    parent = models.ForeignKey(Service, related_name='resources', on_delete=models.CASCADE)


class Project(models.Model):
    name = models.CharField(_('name'), max_length=50)
    data = models.TextField(_('data'), null=True, blank=True)
    service = models.ForeignKey(Service, null=True, blank=True,
                                on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')
