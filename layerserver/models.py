import logging
import os
from slugify import slugify
import shutil

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.gis.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from model_utils import Choices

from .mixins import BaseLayerMixin, StyleMixin
import layerserver.model_legacy as model_legacy
from giscube.db.utils import get_table_parts
from giscube.utils import unique_service_directory
from giscube.models import DBConnection


logger = logging.getLogger(__name__)


def get_jsonlayer_url(instance, filename):
    file_parts = filename.split('.')
    if (file_parts) > 1:
        filename = '%s.%s' % (
            slugify(''.join(file_parts[:-1])), file_parts[-1])
    else:
        filename = slugify(filename)
    return 'layerserver/geojsonlayer/{0}/{1}'.format(instance.id, filename)


def geojsonlayer_upload_path(instance, filename):
    return unique_service_directory(instance, 'remote.json')


SERVICE_VISIBILITY_CHOICES = [
    ('private', 'Private'),
    ('public', 'Public'),
]


class GeoJsonLayer(BaseLayerMixin, StyleMixin, models.Model):
    url = models.CharField(max_length=255, null=True, blank=True)
    headers = models.TextField(null=True, blank=True)
    data_file = models.FileField(upload_to=geojsonlayer_upload_path,
                                 null=True, blank=True)
    service_path = models.CharField(max_length=255)
    cache_time = models.IntegerField(blank=True, null=True, help_text='In seconds')
    last_fetch_on = models.DateTimeField(null=True, blank=True)
    generated_on = models.DateTimeField(null=True, blank=True)
    visibility = models.CharField(max_length=10, default='private',
                                  help_text='visibility=\'Private\' restricts usage to authenticated users',
                                  choices=SERVICE_VISIBILITY_CHOICES)

    def get_data_file_path(self):
        if self.service_path:
            return os.path.join(
                settings.MEDIA_ROOT, self.service_path, 'data.json')

    @property
    def metadata(self):
        return {
            'description': {
                'title': self.title or '',
                'description': self.description or '',
                'keywords': self.keywords or '',
                'generated_on': self.generated_on or ''
            },
            'style': {
                'shapetype': self.shapetype,
                'shape_radius': str(self.shape_radius),
                'stroke_color': self.stroke_color,
                'stroke_width': str(self.stroke_width),
                'stroke_dash_array': self.stroke_dash_array,
                'fill_color': self.fill_color,
                'fill_opacity': str(self.fill_opacity)
            }
        }

    def save(self, *args, **kwargs):
        self.name = slugify(self.name)
        super(self.__class__, self).save(*args, **kwargs)

    def __str__(self):
        return self.name or self.title

    class Meta:
        """Meta information."""
        verbose_name = _('GeoJSONLayer')
        verbose_name_plural = _('GeoJSONLayers')


@receiver(pre_save, sender=GeoJsonLayer)
def geojsonlayer_pre_save(sender, instance, *args, **kwargs):
    if not hasattr(instance, '_disable_pre_save'):
        instance._disable_pre_save = True
        instance._old_data_file = None
        if instance.pk:
            me = GeoJsonLayer.objects.filter(pk=instance.pk).first()
            instance._old_data = model_to_dict(me)


@receiver(post_delete, sender=GeoJsonLayer)
def geojsonlayer_delete(sender, instance, **kwargs):
    if instance.service_path:
        path = os.path.join(settings.MEDIA_ROOT, instance.service_path)
        if os.path.exists(path):
            shutil.rmtree(path)


class DataBaseLayer(BaseLayerMixin, StyleMixin, models.Model):
    db_connection = models.ForeignKey(
        DBConnection, null=False, blank=False, on_delete=models.PROTECT,
        related_name='db_connections', verbose_name='Database connection')
    slug = models.SlugField(max_length=255, blank=False, null=False,
                            unique=True)
    name = models.CharField(max_length=255, blank=False, null=False)

    table = models.CharField(max_length=255)
    pk_field = models.CharField(max_length=255, blank=False, null=False)
    geom_field = models.CharField(max_length=255, blank=True, null=False)
    srid = models.IntegerField(default=4326, blank=False)
    page_size = models.IntegerField(blank=True, null=True,
                                    help_text=_('Default value is %(page_size)s. Value 0 disables pagination.')
                                    % {'page_size': settings.LAYERSERVER_PAGE_SIZE})
    max_page_size = models.IntegerField(blank=True, null=True,
                                        help_text=_('Default value is %(max_page_size)s')
                                        % {'max_page_size': settings.LAYERSERVER_MAX_PAGE_SIZE})

    anonymous_view = models.BooleanField(_('Can view'), default=False)
    anonymous_add = models.BooleanField(_('Can add'), default=False)
    anonymous_update = models.BooleanField(_('Can update'), default=False)
    anonymous_delete = models.BooleanField(_('Can delete'), default=False)

    def get_model_field(self, field_name):
        if not hasattr(self, '_model_fields'):
            LayerModel = model_legacy.create_dblayer_model(self)
            setattr(self, '_model_fields', LayerModel._meta.get_fields())
        for f in self._model_fields:
            if f.name == field_name:
                return f

    def __str__(self):
        return self.name

    class Meta:
        """Meta information."""
        verbose_name = 'DataBaseLayer'
        verbose_name_plural = 'DataBaseLayers'


@receiver(pre_save, sender=DataBaseLayer)
def pre_dblayer(sender, instance, **kwargs):
    if not instance.pk:
        model = model_legacy.create_dblayer_model(instance)
        if not instance.pk_field:
            instance.pk_field = model._meta.pk.name.split('.')[-1]


@receiver(post_save, sender=DataBaseLayer)
def add_fields(sender, instance, created, **kwargs):
    table_parts = get_table_parts(instance.table)
    table_schema = table_parts['table_schema']
    conn = instance.db_connection.get_connection(schema=table_schema)
    fields = model_legacy.get_fields(conn, instance.table)
    old_fields = []
    if not created:
        old_fields = [field.name for field in instance.fields.all()]
    for field in list(fields.keys()):
        if field not in old_fields:
            db_field = DataBaseLayerField()
            db_field.layer = instance
            db_field.name = field
            db_field.save()
        else:
            if field in old_fields:
                old_fields.remove(field)
    if not created and len(old_fields) > 0:
        DataBaseLayerField.objects.filter(
            layer=instance, name__in=old_fields).delete()


DATA_TYPES = {
    models.GeometryField: 'geometry',
    models.GenericIPAddressField: 'string',
    models.UUIDField: 'string',
    models.DateField: 'date',
    models.TimeField: 'time',
    models.DateTimeField: 'datetime',
    models.AutoField: 'number',
    models.NullBooleanField: 'boolean',
    models.BooleanField: 'boolean',
    models.DecimalField: 'number',
    models.FloatField: 'number',
    models.IntegerField: 'number',
    models.TextField: 'string',
    models.CharField: 'string',
}


class DataBaseLayerField(models.Model):

    WIDGET_CHOICES = Choices(
        ('auto', 'Auto'),
        ('choices', 'Choices, one line per value'),
        ('image', 'Image'),
        ('linkedfield', 'Linked Field'),
        ('sqlchoices', 'SQL choices'),
    )

    layer = models.ForeignKey(
        DataBaseLayer, null=False, blank=False,
        related_name='fields', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False, null=False)
    label = models.CharField(max_length=255, blank=True, null=True)
    search = models.BooleanField(default=True)
    fullsearch = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)
    widget = models.CharField(max_length=25, blank=False,
                              choices=WIDGET_CHOICES, default=WIDGET_CHOICES.auto)
    widget_options = models.TextField(null=True, blank=True)

    @cached_property
    def field_type(self):
        field_type = None
        model_field = self.get_model_field()
        if model_field:
            type_ = type(model_field)
            field_type = DATA_TYPES.get(type_)
            if not field_type:
                for k, v in DATA_TYPES.items():
                    if isinstance(model_field, k):
                        field_type = v
                        break
        return field_type

    @cached_property
    def null(self):
        null = None
        model_field = self.get_model_field()
        if model_field:
            null = model_field.null
        return null

    @cached_property
    def size(self):
        size = None
        model_field = self.get_model_field()
        if model_field and self.field_type:
            if self.field_type == 'string':
                if hasattr(model_field, 'max_length'):
                    size = model_field.max_length
            elif self.field_type == 'number':
                if isinstance(model_field, models.DecimalField):
                    size = model_field.max_digits
        return size

    @cached_property
    def decimals(self):
        decimals = None
        model_field = self.get_model_field()
        if model_field and self.field_type:
            if self.field_type == 'number':
                if isinstance(model_field, models.IntegerField):
                    decimals = 0
                elif isinstance(model_field, models.DecimalField):
                    decimals = model_field.decimal_places
        return decimals

    def get_model_field(self):
        if not hasattr(self, '_model_field'):
            self._model_field = None
            try:
                self._model_field = self.layer.get_model_field(self.name)
            except Exception as e:
                logger.warning(str(e), exc_info=True)
        return self._model_field

    def __str__(self):
        return self.label or self.name

    class Meta:
        verbose_name = _('Field')
        verbose_name_plural = _('Fields')


class DataBaseLayerReference(models.Model):
    layer = models.ForeignKey(DataBaseLayer, null=False, blank=False, related_name='references',
                              on_delete=models.CASCADE)
    service = models.ForeignKey('qgisserver.Service', null=False, blank=False, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.service.title or self.service.name)

    class Meta:
        verbose_name = _('Reference')
        verbose_name_plural = _('References')
        unique_together = ('layer', 'service',)


class DBLayerGroup(models.Model):
    layer = models.ForeignKey(DataBaseLayer, related_name='layer_groups', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name=_('Group'), on_delete=models.CASCADE)
    can_view = models.BooleanField(_('Can view'), default=True)
    can_add = models.BooleanField(_('Can add'), default=True)
    can_update = models.BooleanField(_('Can update'), default=True)
    can_delete = models.BooleanField(_('Can delete'), default=True)

    def __str__(self):
        return self.group.name

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')


class DBLayerUser(models.Model):
    layer = models.ForeignKey(DataBaseLayer, related_name='layer_users', on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name=_('User'), on_delete=models.CASCADE)
    can_view = models.BooleanField(_('Can view'), default=True)
    can_add = models.BooleanField(_('Can add'), default=True)
    can_update = models.BooleanField(_('Can update'), default=True)
    can_delete = models.BooleanField(_('Can delete'), default=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
