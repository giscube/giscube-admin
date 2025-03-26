import os
import shutil

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver
from django.utils.translation import gettext as _

from giscube.model_mixins import MetadataModelMixin, ResourceModelMixin
from giscube.models import Category, Server
from giscube.tilecache.models_mixins import TileCacheModelMixin
from giscube.utils import url_slash_join
from giscube.validators import validate_options_json_format
from qgisserver.utils import deactivate_services, unique_service_directory


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


def project_unique_service_directory(instance, filename):
    filename = os.path.join('mapdata', filename)
    return unique_service_directory(instance, filename)


class Service(TileCacheModelMixin, models.Model):
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='qgisserver_services')
    name = models.CharField(_('name'), max_length=50, unique=True)
    title = models.CharField(_('title'), max_length=100, null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)
    keywords = models.CharField(_('keywords'), max_length=200, null=True, blank=True)
    project_file = models.FileField(
        _('project file'), upload_to=project_unique_service_directory)
    service_path = models.CharField(_('service path'), max_length=255)
    active = models.BooleanField(_('active'), default=True, help_text='Enable/disable usage')
    visible_on_geoportal = models.BooleanField(_('visible on geoportal'), default=False)
    wms_getfeatureinfo_enabled = models.BooleanField(
        _('WMS GetFeatureInfo enabled'), default=True
    )
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

    tilecache_transparent = models.BooleanField(_('force transparent'), default=True)
    wms_single_image = models.BooleanField(_('prefer single image'), default=False)

    anonymous_view = models.BooleanField(_('anonymous users can view'), default=False)
    anonymous_write = models.BooleanField(_('anonymous users can write'), default=False)
    authenticated_user_view = models.BooleanField(_('authenticated users can view'), default=False)
    authenticated_user_write = models.BooleanField(_('authenticated users can write'), default=False)

    choose_individual_layers = models.BooleanField(_("choose individual layers"), default=False)
    read_layers_automatically = models.BooleanField(_("read layers automatically"), default=False)
    layers = models.TextField(_('layers'), null=True, blank=True)

    help_text = '%s %s' % (_('Field between curly braces. e.g.'), '{%s}' % _('street'))
    popup = models.TextField(_('popup'), blank=True, null=True, help_text=help_text)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

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
    def wms_url(self):
        return '%s?service=WMS&version=1.1.1&request=GetCapabilities' % self.service_url

    @property
    def service_internal_url(self):
        if self.project_file:
            server_url = settings.GISCUBE_QGIS_SERVER_URL
            mapfile = "map=%s" % self.project_file.path
            if '?' not in server_url:
                server_url = '%s?' % server_url
            if not server_url.endswith('?'):
                server_url = '%s&' % server_url
            url = "%s%s" % (server_url, mapfile)
            return url
    

    def get_filters(self):
        from .serializers import ServiceFilterSerializer
        filters = []
        for filter in self.filters.all():
            serializer = ServiceFilterSerializer(filter)
            filters.append(serializer.data)
        return filters


    def __str__(self):
        return str(self.title or self.name)

    class Meta:
        verbose_name = _('Service')
        verbose_name_plural = _('Services')


@receiver(models.signals.post_delete, sender=Service)
def auto_delete_service_path_on_delete(sender, instance, **kwargs):
    """
    Delete the project file if the service is deleted
    """
    if instance.service_path:
        path = os.path.join(settings.MEDIA_ROOT, instance.service_path)
        if os.path.isdir(path):
            shutil.rmtree(path)


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
        if old_file and os.path.exists(old_file.path) and os.path.isfile(old_file.path):
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


class ServiceFilter(models.Model):
    service = models.ForeignKey(Service, related_name='filters', on_delete=models.CASCADE)
    title = models.CharField(_('title'), max_length=50, null=True, blank=True)
    layer = models.CharField(_('layer'), max_length=255, null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)
    filter = models.CharField(_('field'), max_length=255, null=True, blank=True)


class ServiceMetadata(MetadataModelMixin):
    parent = models.OneToOneField(Service, on_delete=models.CASCADE, primary_key=True, related_name='metadata')


class ServiceResource(ResourceModelMixin):
    parent = models.ForeignKey(Service, related_name='resources', on_delete=models.CASCADE)


class ServiceGroupPermission(models.Model):
    service = models.ForeignKey(Service, related_name='group_permissions', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name=_('Group'), on_delete=models.CASCADE)
    can_view = models.BooleanField(_('Can view'), default=True)
    can_write = models.BooleanField(_('Can write'), default=True)

    def __str__(self):
        return self.group.name

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')


class ServiceUserPermission(models.Model):
    service = models.ForeignKey(Service, related_name='user_permissions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name=_('User'), on_delete=models.CASCADE)
    can_view = models.BooleanField(_('Can view'), default=True)
    can_write = models.BooleanField(_('Can write'), default=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')


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
