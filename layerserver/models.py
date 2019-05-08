import logging
import os
import shutil

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.gis.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext as _

from model_utils import Choices

from .model_legacy import ImageWithThumbnailField
from .models_mixins import BaseLayerMixin, PopupMixin, ShapeStyleMixin, StyleMixin
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
    ('private', _('Private')),
    ('public', _('Public')),
]


class GeoJsonLayer(BaseLayerMixin, ShapeStyleMixin, PopupMixin, models.Model):
    url = models.CharField(_('url'), max_length=255, null=True, blank=True)
    headers = models.TextField(_('headers'), null=True, blank=True)
    data_file = models.FileField(_('data file'), upload_to=geojsonlayer_upload_path,
                                 null=True, blank=True)
    service_path = models.CharField(_('service path'), max_length=255)
    cache_time = models.IntegerField(_('cache time'), blank=True, null=True, help_text='In seconds')
    last_fetch_on = models.DateTimeField(_('last fetch on'), null=True, blank=True)
    generated_on = models.DateTimeField(_('generated on'), null=True, blank=True)
    visibility = models.CharField(_('visibility'), max_length=10, default='private',
                                  help_text=_('visibility=\'Private\' restricts usage to authenticated users'),
                                  choices=SERVICE_VISIBILITY_CHOICES)
    fields = models.TextField(blank=True, null=True)

    def get_data_file_path(self):
        if self.service_path:
            return os.path.join(
                settings.MEDIA_ROOT, self.service_path, 'data.json')

    @property
    def metadata(self):
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
                'popup': self.popup
            }
        }

    def get_default_popup(self):
        fields = {}
        if self.fields is not None:
            for field in self.fields.split(','):
                fields[field] = field
        return self.get_default_popup_content(fields)

    def save(self, *args, **kwargs):
        self.name = slugify(self.name)
        if (self.popup is None or self.popup == ''):
            self.popup = self.get_default_popup()
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


class DataBaseLayer(BaseLayerMixin, ShapeStyleMixin, PopupMixin, models.Model):
    db_connection = models.ForeignKey(
        DBConnection, null=False, blank=False, on_delete=models.PROTECT,
        related_name='db_connections', verbose_name='Database connection')
    name = models.CharField(_('name'), max_length=255, blank=False, null=False, unique=True)
    table = models.CharField(_('table'), max_length=255, blank=False, null=False)
    pk_field = models.CharField(_('pk field'), max_length=255, blank=True, null=False)
    geom_field = models.CharField(_('geom field'), max_length=255, blank=False, null=False)
    srid = models.IntegerField(_('srid'), default=4326, blank=False)
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

    def get_model_field(self, field_name):
        if not hasattr(self, '_model_fields'):
            LayerModel = model_legacy.create_dblayer_model(self)
            setattr(self, '_model_fields', LayerModel._meta.get_fields())
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
        self.name = slugify(self.name)
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
        model = model_legacy.create_dblayer_model(instance)
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
    fields = model_legacy.get_fields(conn, instance.table)
    old_fields = []
    if not created:
        old_fields = [field.name for field in instance.fields.all()]
    for field in list(fields.keys()):
        if field not in old_fields:
            db_field = DataBaseLayerField()
            db_field.layer = instance
            db_field.name = field
            db_field.blank = fields[field].null
            db_field.save()
        else:
            if field in old_fields:
                old_fields.remove(field)
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
    if instance.popup is None or instance.popup.strip(' \t\n\r') == '':
        instance.popup = instance.get_default_popup()
        changes += 1
    if changes > 0:
        instance._disable_signal_add_fields = True
        instance.save()


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
    ImageWithThumbnailField: 'image',
}


class DataBaseLayerField(models.Model):

    WIDGET_CHOICES = Choices(
        ('auto', _('Auto')),
        ('choices', _('Choices, one line per value')),
        ('date', _('Date')),
        ('image', _('Image')),
        ('linkedfield', _('Linked Field')),
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
    widget_options = models.TextField(_('srid'), null=True, blank=True)

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
