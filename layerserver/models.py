import json
import logging
import os
import shutil

from model_utils import Choices

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext as _

from giscube.db.utils import get_table_parts
from giscube.model_mixins import MetadataModelMixin, ResourceModelMixin
from giscube.models import DBConnection
from giscube.storage import OverwriteStorage
from giscube.utils import RecursionException, check_recursion, unique_service_directory

from . import model_legacy
from .fields import ImageWithThumbnailField
from .mapserver import SUPORTED_SHAPE_TYPES
from .models_mixins import BaseLayerMixin, ClusterMixin, PopupMixin, ShapeStyleMixin, StyleMixin, TooltipMixin
from .tasks import async_generate_mapfile
from .widgets import widgets_types


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


class GeoJsonLayer(BaseLayerMixin, ShapeStyleMixin, PopupMixin, TooltipMixin, ClusterMixin, models.Model):
    url = models.CharField(_('url'), max_length=255, null=True, blank=True)
    headers = models.TextField(_('headers'), null=True, blank=True)
    data_file = models.FileField(_('data file'), upload_to=geojsonlayer_upload_path,
                                 null=True, blank=True)
    service_path = models.CharField(_('service path'), max_length=255)
    help_text = _('Time in seconds where the file is served from cache')
    cache_time = models.PositiveIntegerField(_('cache time'), blank=True, null=True, help_text=help_text)
    help_text = _('Maximum outdated time in seconds for the cache file')
    max_outdated_time = models.PositiveIntegerField(
        _('maximum outdated time'), blank=True, null=True, help_text=help_text)
    last_fetch_on = models.DateTimeField(_('last fetch on'), null=True, blank=True)
    generated_on = models.DateTimeField(_('generated on'), null=True, blank=True)
    anonymous_view = models.BooleanField(_('anonymous users can view'), default=False)
    authenticated_user_view = models.BooleanField(_('authenticated users can view'), default=False)
    fields = models.TextField(blank=True, null=True)
    design_from = models.ForeignKey('self', related_name='design_from_childs', verbose_name=_('get design from'),
                                    blank=True, null=True, on_delete=models.SET_NULL)
    legend = models.TextField(_('legend'), null=True, blank=True)

    def get_data_file_path(self):
        if self.service_path:
            return os.path.join(
                settings.MEDIA_ROOT, self.service_path, 'data.json')

    def _get_popup(self, done=None):
        done = [] if done is None else done
        popup = None
        if self.design_from is None:
            popup = self.popup if self.popup not in (None, '') else None
        elif self.design_from.pk not in done:
            done.append(self.design_from.pk)
            popup = self.design_from._get_popup(done)
        return popup

    def _get_tooltip(self, done=None):
        done = [] if done is None else done
        tooltip = None
        if self.design_from is None:
            tooltip = self.tooltip if self.tooltip not in (None, '') else None
        elif self.design_from and self.design_from.pk not in done:
            done.append(self.design_from.pk)
            tooltip = self.design_from._get_tooltip(done)
        return tooltip

    @property
    def geojson_metadata(self):
        from .serializers import style_representation, style_rules_representation
        return {
            'description': {
                'title': self.title or '',
                'description': self.description or '',
                'keywords': self.keywords or '',
                'generated_on': self.generated_on or ''
            },
            'style': style_representation(self),
            'style_rules': style_rules_representation(self),
            'design': {
                'interactive': self.interactive,
                'popup': self._get_popup() if self.interactive else None,
                'tooltip': self._get_tooltip() if self.interactive else None,
                'cluster': json.loads(self.cluster_options or '{}') if self.cluster_enabled else None
            }
        }

    def get_default_popup(self):
        fields = {}
        if self.fields is not None:
            for field in list(filter(None, self.fields.split(','))):
                fields[field] = field
        return self.get_default_popup_content(fields)

    def clean(self):
        try:
            check_recursion('design_from', self, [])
        except RecursionException as e:
            raise ValidationError(str(e))

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name or self.title

    class Meta:
        """Meta information."""
        verbose_name = _('GeoJSONLayer')
        verbose_name_plural = _('GeoJSONLayers')


def refresh_childs(layer):
    from .tasks import async_geojsonlayer_refresh
    for x in layer.design_from_childs.all():
        async_geojsonlayer_refresh.delay(x.pk, force_refresh_data_file=False, generate_popup=False)


@receiver(post_save, sender=GeoJsonLayer)
def refresh_design(sender, instance, created, **kwargs):
    transaction.on_commit(
        lambda: refresh_childs(instance)
    )


@receiver(pre_save, sender=GeoJsonLayer)
def geojsonlayer_pre_save(sender, instance, *args, **kwargs):
    if not hasattr(instance, '_disable_pre_save'):
        instance._disable_pre_save = True
        instance._old_data_file = None
        if instance.pk:
            me = GeoJsonLayer.objects.filter(pk=instance.pk).first()
            if me:  # fix manage.py loaddata
                instance._old_data = model_to_dict(me)


@receiver(post_delete, sender=GeoJsonLayer)
def geojsonlayer_delete(sender, instance, **kwargs):
    if instance.service_path:
        path = os.path.join(settings.MEDIA_ROOT, instance.service_path)
        if os.path.exists(path):
            shutil.rmtree(path)


class GeoJsonLayerGroupPermission(models.Model):
    layer = models.ForeignKey(GeoJsonLayer, related_name='group_permissions', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name=_('Group'), on_delete=models.CASCADE)
    can_view = models.BooleanField(_('Can view'), default=True)

    def __str__(self):
        return self.group.name

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')


class GeoJsonLayerUserPermission(models.Model):
    layer = models.ForeignKey(GeoJsonLayer, related_name='user_permissions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name=_('User'), on_delete=models.CASCADE)
    can_view = models.BooleanField(_('Can view'), default=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')


class GeoJsonLayerMetadata(MetadataModelMixin):
    parent = models.OneToOneField(GeoJsonLayer, on_delete=models.CASCADE, primary_key=True, related_name='metadata')


class GeoJsonLayerResource(ResourceModelMixin):
    parent = models.ForeignKey(GeoJsonLayer, related_name='resources', on_delete=models.CASCADE)


COMPARATOR_CHOICES = (
    ('=', '=',),
    ('!=', '!=',),
    ('>', '>',),
    ('>=', '>=',),
    ('<', '<',),
    ('<=', '<=',)
)


class GeoJsonLayerStyleRule(StyleMixin, models.Model):
    layer = models.ForeignKey(GeoJsonLayer, related_name='rules', on_delete=models.CASCADE)
    field = models.CharField(_('field'), max_length=50, blank=False, null=False)
    comparator = models.CharField(_('comparator'), max_length=3, blank=False, null=False, choices=COMPARATOR_CHOICES)
    value = models.CharField(_('value'), max_length=255, blank=True, null=True)
    order = models.PositiveIntegerField(_('order'), blank=True, null=True)

    def __str__(self):
        return '%s %s %s' % (self.field, self.comparator, self.value or '')

    class Meta:
        ordering = ('layer', 'order',)
        verbose_name = _('Style rule')
        verbose_name_plural = _('Style rules')


def databaselayer_mapfile_upload_path(instance, filename):
    return unique_service_directory(instance, 'wms.map')


DATA_FILTER_STATUS_CHOICES = Choices(
    ('enabled', _('Enabled'),),
    ('disabled', _('Error misconfigured'),),
)


class DataBaseLayer(BaseLayerMixin, ShapeStyleMixin, PopupMixin, TooltipMixin, ClusterMixin, models.Model):
    db_connection = models.ForeignKey(
        DBConnection, null=False, blank=False, on_delete=models.PROTECT,
        related_name='layers', verbose_name='Database connection')
    name = models.CharField(_('name'), max_length=255, blank=False, null=False, unique=True)
    table = models.CharField(_('table'), max_length=255, blank=False, null=False)
    data_filter = JSONField(_('data filter'), blank=True, null=True, default=dict)
    data_filter_status = models.CharField(choices=DATA_FILTER_STATUS_CHOICES,
                                          max_length=50, null=True, blank=True, editable=False)
    data_filter_error = models.TextField(null=True, blank=True, editable=False)

    pk_field = models.CharField(_('pk field'), max_length=255, blank=True, null=False)
    geom_field = models.CharField(_('geom field'), max_length=255, blank=True, null=True)
    srid = models.IntegerField(_('srid'), blank=True, null=True)
    allow_page_size_0 = models.BooleanField(_('Allow page size=0 (Disables pagination)'), default=False)
    page_size = models.IntegerField(
        _('page size'), blank=True, null=True, help_text=_('Default value is %s. Value 0 disables pagination.') %
        settings.LAYERSERVER_PAGE_SIZE)
    max_page_size = models.IntegerField(
        _('maximum page size'), blank=True, null=True, help_text=_('Default value is %s') %
        settings.LAYERSERVER_MAX_PAGE_SIZE)

    list_fields = models.TextField(_('list fields'), blank=True, null=True)
    form_fields = models.TextField(_('form fields'), blank=True, null=True)

    anonymous_view = models.BooleanField(_('Can view'), default=False)
    anonymous_add = models.BooleanField(_('Can add'), default=False)
    anonymous_update = models.BooleanField(_('Can update'), default=False)
    anonymous_delete = models.BooleanField(_('Can delete'), default=False)

    service_path = models.CharField(max_length=255, null=True, blank=True)
    mapfile = models.FileField(
        null=True, blank=True, storage=OverwriteStorage(), upload_to=databaselayer_mapfile_upload_path)

    wms_as_reference = models.BooleanField(_('Use generated WMS as reference'), default=False)
    legend = models.TextField(_('legend'), null=True, blank=True)

    def get_model_field(self, field_name):
        if not hasattr(self, '_model_fields'):
            with model_legacy.ModelFactory(self, exclude_enabled=False) as LayerModel:
                self._model_fields = LayerModel._meta.get_fields()
        for f in self._model_fields:
            if f.name == field_name:
                return f

    def get_default_popup(self):
        fields = {}
        for field in self.fields.filter(enabled=True).exclude(name=self.geom_field):
            fields[field.name] = field.label or field.name
        return self.get_default_popup_content(fields)

    def get_page_size(self):
        return self.page_size if self.page_size else settings.LAYERSERVER_PAGE_SIZE

    def get_max_page_size(self):
        return self.max_page_size if self.max_page_size else settings.LAYERSERVER_MAX_PAGE_SIZE

    def save(self, *args, **kwargs):
        if self.geom_field is not None and self.srid is None:
            self.srid = 4326
        if self.service_path is None and self.name:
            unique_service_directory(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        """Meta information."""
        verbose_name = 'DataBaseLayer'
        verbose_name_plural = 'DataBaseLayers'


@receiver(pre_save, sender=DataBaseLayer)
def pre_dblayer(sender, instance, **kwargs):
    if not instance.pk:
        with model_legacy.ModelFactory(instance) as model:
            if not instance.pk_field:
                instance.pk_field = model._meta.pk.name.split('.')[-1]


@receiver(post_save, sender=DataBaseLayer)
def add_fields(sender, instance, created, **kwargs):
    if hasattr(instance, '_disable_signal_add_fields'):
        delattr(instance, '_disable_signal_add_fields')
        return None

    table_parts = get_table_parts(instance.table)
    table_schema = table_parts['table_schema']
    conn = instance.db_connection.get_connection(schema=table_schema)
    fields = model_legacy.get_fields(conn, instance.table, instance.pk_field)
    old_fields = []
    if not created:
        old_fields = [field.name for field in instance.fields.all()]
    for field_name, field in fields.items():
        if field_name not in old_fields:
            db_field = DataBaseLayerField()
            db_field.layer = instance
            db_field.name = field_name
            db_field.blank = field['kwargs']['blank']
            db_field.fullsearch = DataBaseLayerField.get_default_for_fullsearch(field)
            db_field.save()
        else:
            if field_name in old_fields:
                old_fields.remove(field_name)
    if not created and len(old_fields) > 0:
        DataBaseLayerField.objects.filter(
            layer=instance, name__in=old_fields).delete()

    changes = 0
    if instance.list_fields is None or instance.list_fields.strip(' \t\n\r') == '':
        list_fields = list(fields.keys())
        list_fields.sort()
        try:
            list_fields.remove(instance.geom_field)
        except Exception:
            pass
        instance.list_fields = ','.join(list_fields)
        changes += 1
    if instance.form_fields is None or instance.form_fields.strip(' \t\n\r') == '':
        form_fields = list(fields.keys())
        form_fields.sort()
        try:
            form_fields.remove(instance.geom_field)
        except Exception:
            pass
        instance.form_fields = ','.join(form_fields)
        changes += 1
    if instance.geom_field is not None and (instance.popup is None or instance.popup.strip(' \t\n\r') == ''):
        instance.popup = instance.get_default_popup()
        changes += 1
    if changes > 0:
        instance._disable_signal_add_fields = True
        instance.save()


def _generate_mapfile(obj):
    if obj.shapetype in SUPORTED_SHAPE_TYPES and obj.geom_field is not None:
        async_generate_mapfile.delay(obj.pk)


@receiver(post_save, sender=DataBaseLayer)
def generate_mapfile(sender, instance, created, **kwargs):
    if not hasattr(instance, '_mapfile_generated') and not created:
        transaction.on_commit(
            lambda: _generate_mapfile(instance)
        )


@receiver(post_save, sender=DBConnection)
def generate_mapfiles(sender, instance, created, **kwargs):
    if not created:
        transaction.on_commit(
            lambda: [_generate_mapfile(layer) for layer in instance.layers.all()]
        )


@receiver(post_save, sender=DataBaseLayer)
def unregister_model(sender, instance, created, **kwargs):
    transaction.on_commit(
        lambda: model_legacy.ModelFactory(instance).try_unregister_model()
    )


class DataBaseLayerMetadata(MetadataModelMixin):
    parent = models.OneToOneField(DataBaseLayer, on_delete=models.CASCADE, primary_key=True, related_name='metadata')


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
    ImageWithThumbnailField: 'string',
}


class DataBaseLayerField(models.Model):
    WIDGET_CHOICES = Choices(
        ('auto', _('Auto')),
        ('choices', _('Choices, one line per value')),
        ('creationdate', _('Creation date')),
        ('creationdatetime', _('Creation datetime')),
        ('creationuser', _('Creation user')),
        ('date', _('Date')),
        ('datetime', _('Date time')),
        ('distinctvalues', _('Distinct values')),
        ('foreignkey', _('Foreign key')),
        ('image', _('Image')),
        ('linkedfield', _('Linked Field')),
        ('modificationdate', _('Modification date')),
        ('modificationdatetime', _('Modification datetime')),
        ('modificationuser', _('Modification user')),
        ('sqlchoices', _('SQL choices')),
    )

    layer = models.ForeignKey(
        DataBaseLayer, null=False, blank=False,
        related_name='fields', on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=255, blank=False, null=False)
    label = models.CharField(_('label'), max_length=255, blank=True, null=True)
    search = models.BooleanField(_('search'), default=True)
    fullsearch = models.BooleanField(_('full search'), default=True)
    enabled = models.BooleanField(_('enabled'), default=True)
    readonly = models.BooleanField(_('readonly'), default=False)
    blank = models.BooleanField(_('blank'), default=True)
    widget = models.CharField(
        _('widget'), max_length=25, blank=False, choices=WIDGET_CHOICES, default=WIDGET_CHOICES.auto)
    widget_options = models.TextField(_('widget options'), null=True, blank=True)

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
                decimals = 0
                if isinstance(model_field, models.DecimalField):
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

    @staticmethod
    def get_default_for_fullsearch(field):
        return not (issubclass(field.get('klass', None), models.fields.GeometryField))

    def clean(self):
        if self.name == self.layer.geom_field and not self.enabled:
            raise ValidationError({'enabled': _('Geom field must be enabled')})
        if self.name == self.layer.geom_field and self.fullsearch:
            raise ValidationError({'enabled': _('full search is not available for geom fields')})
        if self.name == self.layer.pk_field and not self.enabled:
            raise ValidationError({'enabled': _('pk field must be enabled')})

    class Meta:
        verbose_name = _('Field')
        verbose_name_plural = _('Fields')
        ordering = ['layer', 'name']


class DataBaseLayerVirtualField(models.Model):
    WIDGET_CHOICES = Choices(
        ('relation1n', _('1:N Relation')),
        ('linkedfield', _('Linked Field')),
    )

    layer = models.ForeignKey(
        DataBaseLayer, null=False, blank=False, related_name='virtual_fields', on_delete=models.CASCADE)
    name = models.CharField(_('name'), max_length=255, blank=False, null=False)
    label = models.CharField(_('label'), max_length=255, blank=True, null=True)
    enabled = models.BooleanField(_('enabled'), default=True)
    widget = models.CharField(_('widget'), max_length=25, blank=False, choices=WIDGET_CHOICES)
    widget_options = models.TextField(_('widget options'), null=True, blank=True)

    @cached_property
    def config(self):
        data = {}
        try:
            data = json.loads(self.widget_options)
        except Exception:
            raise Exception('Invalid configuration for DataBaseLayerVirtualField: %s.%s' % (
                self.layer.name, self.name))
        return data

    @cached_property
    def widget_class(self):
        return widgets_types[self.widget]

    def __str__(self):
        return self.label or self.name

    class Meta:
        verbose_name = _('Virtual Field')
        verbose_name_plural = _('Virtual Fields')
        ordering = ['layer', 'name']


class DataBaseLayerStyleRule(StyleMixin, models.Model):
    layer = models.ForeignKey(DataBaseLayer, related_name='rules', on_delete=models.CASCADE)
    field = models.CharField(_('field'), max_length=50, blank=False, null=False)
    comparator = models.CharField(_('comparator'), max_length=3, blank=False, null=False, choices=COMPARATOR_CHOICES)
    value = models.CharField(_('value'), max_length=255, blank=False, null=False,)
    order = models.PositiveIntegerField(_('order'), blank=True, null=True)

    def __str__(self):
        return '%s %s %s' % (self.field, self.comparator, self.value or '')

    class Meta:
        ordering = ('layer', 'order',)
        verbose_name = _('Style rule')
        verbose_name_plural = _('Style rules')


class DataBaseLayerReference(models.Model):
    IMAGE_FORMAT_CHOICES = Choices(
        ('image/png', 'PNG'),
        ('image/jpeg', 'JPEG'),
    )
    layer = models.ForeignKey(DataBaseLayer, null=False, blank=False, related_name='references',
                              on_delete=models.CASCADE)
    service = models.ForeignKey('qgisserver.Service', null=False, blank=False, on_delete=models.CASCADE)
    format = models.CharField(
        _('format'), max_length=25, blank=False, choices=IMAGE_FORMAT_CHOICES, default='image/jpeg')
    transparent = models.BooleanField(_('transparent'), null=True)
    refresh = models.BooleanField(_('refresh on data changes'), default=False)

    def __str__(self):
        return str(self.service.title or self.service.name)

    class Meta:
        verbose_name = _('Reference')
        verbose_name_plural = _('References')
        unique_together = ('layer', 'service',)


class DataBaseLayerResource(ResourceModelMixin):
    parent = models.ForeignKey(DataBaseLayer, related_name='resources', on_delete=models.CASCADE)


class DBLayerGroup(models.Model):
    layer = models.ForeignKey(DataBaseLayer, related_name='group_permissions', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name=_('Group'), on_delete=models.CASCADE)
    can_view = models.BooleanField(_('Can view'), default=True)
    can_add = models.BooleanField(_('Can add'), default=True)
    can_update = models.BooleanField(_('Can update'), default=True)
    can_delete = models.BooleanField(_('Can delete'), default=True)
    data_filter = JSONField(_('data filter'), blank=True, null=True, default=dict)
    data_filter_status = models.CharField(choices=DATA_FILTER_STATUS_CHOICES,
                                          max_length=50, null=True, blank=True, editable=False)
    data_filter_error = models.TextField(null=True, blank=True, editable=False)

    def __str__(self):
        return self.group.name

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')


class DBLayerUser(models.Model):
    layer = models.ForeignKey(DataBaseLayer, related_name='user_permissions', on_delete=models.CASCADE)
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
