import logging
import os
import time
import uuid

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import connections, models
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.translation import gettext as _

from .model_mixins import MetadataModelMixin
from .storage import OverwriteStorage
from .utils import RecursionException, check_recursion, get_cls
from .validators import validate_options_json_format


logger = logging.getLogger(__name__)


class Category(models.Model):
    SEPARATOR = ' > '
    name = models.CharField(_('name'), max_length=50)
    color = models.CharField(_('color'), max_length=50, null=True, blank=True)
    parent = models.ForeignKey(
        'Category', verbose_name=_('parent category'), null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    @property
    def title(self):
        names = []
        parent = self
        while parent is not None:
            names.insert(0, parent.name)
            parent = parent.parent
        return self.SEPARATOR.join(names)

    def clean(self):
        try:
            check_recursion('parent', self)
        except RecursionException as e:
            raise ValidationError(e.message)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title


DB_CONNECTION_ENGINE_CHOICES = [
    ('django.contrib.gis.db.backends.postgis', 'Postgis'),
]


class DBConnection(models.Model):
    alias = models.CharField(_('alias'), max_length=255, null=True, blank=True)
    engine = models.CharField(_('engine'), max_length=255,
                              choices=DB_CONNECTION_ENGINE_CHOICES)
    name = models.CharField(_('Database name'), max_length=100, null=False, blank=False)
    user = models.CharField(_('user'), max_length=100, null=True, blank=True)
    password = models.CharField(_('password'), max_length=255, null=True, blank=True)
    host = models.CharField(_('host'), max_length=100, null=True, blank=True)
    port = models.CharField(_('port'), max_length=20, null=True, blank=True)

    def db_conf(self, schema=None):
        db = {}
        db['ENGINE'] = self.get_engine(self.engine)
        db['NAME'] = self.name
        if self.user:
            db['USER'] = self.user
        if self.password:
            db['PASSWORD'] = self.password
        if self.host:
            db['HOST'] = self.host
        if self.port:
            db['PORT'] = self.port
        if schema:
            postgres_engines = [
                'giscube.db.backends.postgis',
            ]
            if self.engine in (postgres_engines):
                db['OPTIONS'] = {
                    'options': '-c search_path=%s,public' % schema
                }

        return db

    def connection_name(self, schema=None):
        if schema:
            return 'giscube_connection_schema_%s_%s' % (self.pk, schema)
        else:
            return 'giscube_connection_%s' % self.pk

    def check_connection(self):
        db_conf = self.db_conf()
        name = 'giscube_connection_tmp_%s' % time.time()
        settings.DATABASES[name] = db_conf

        db_conn = connections[name]
        res = None
        try:
            db_conn.cursor()
        except Exception:
            res = False
        else:
            db_conn.close()
            res = True
        del connections[name]
        del settings.DATABASES[name]
        return res

    def get_connection(self, schema=None):
        self.schema = schema
        db_conf = self.db_conf(schema)
        name = self.connection_name(schema)
        if not(name in settings.DATABASES):
            settings.DATABASES[name] = db_conf
        return connections[name]

    def get_engine(self, engine):
        if engine == 'django.contrib.gis.db.backends.postgis':
            engine = 'giscube.db.backends.postgis'
        return engine

    def geometry_columns(self):
        rows = []
        conn = self.get_connection()
        GeometryColumns = conn.ops.geometry_columns()
        qs = GeometryColumns.objects.using(self.connection_name()).all()
        for column in qs:
            row = model_to_dict(column)
            label = ''
            if row['f_table_schema'] != '':
                label = '"%s".' % row['f_table_schema']
            label = '%s"%s"."%s" (%s, %s)' % (
                label, row['f_table_name'], row['f_geometry_column'], row['type'], row['srid'])
            row['label'] = label
            rows.append(row)
        return rows

    def full_clean(self, *args, **kwargs):
        from django.core.validators import ValidationError
        if not self.check_connection():
            raise ValidationError(_('Database connection error'))

    def __str__(self):
        return '%s' % self.alias or self.name

    class Meta:
        """Meta information."""
        verbose_name = _('Database connection')
        verbose_name_plural = _('Database connections')


class Server(models.Model):
    name = models.CharField(_('name'), max_length=50, unique=True)
    url = models.URLField(_('url'), null=True, blank=True)
    token = models.CharField(_('token'), max_length=255, null=True, blank=True)
    this_server = models.BooleanField(_('this server'), default=False)

    class Meta:
        """Meta information."""
        verbose_name = _('Server connection')
        verbose_name_plural = _('Server connections')

    def __str__(self):
        return '%s' % self.name


def user_asset_upload_to(instance, filename, uuid_folder=None):
    storage_class = get_cls('USER_ASSETS_STORAGE_CLASS')
    storage = storage_class(location='user/assets/{0}'.format(instance.user.id))

    dirs = []
    files = []
    try:
        dirs, files = storage.listdir('.')
    except Exception as e:
        if settings.DEBUG:
            logger.warning(str(e), exc_info=True)
    else:
        for dir in dirs:
            path = 'user/assets/{0}/{1}/{2}'.format(instance.user.id, dir, filename)
            if not storage.exists(path):
                return path
    return 'user/assets/{0}/{1}/{2}'.format(instance.user.id, instance.uuid, filename)


class UserAsset(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    file = models.FileField(_('file'), max_length=255, upload_to=user_asset_upload_to)
    created = models.DateTimeField(_('creation datetime'), auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='assets', on_delete=models.CASCADE)

    def delete(self, *args, **kwargs):
        super(UserAsset, self).delete(*args, **kwargs)
        if self.file:
            folder = os.path.dirname(self.file.name)
            self.file.delete(save=False)
            delete_parent = None
            if isinstance(self.file.storage, FileSystemStorage):
                dirs, files = self.file.storage.listdir(folder)
                if len(files) == 0:
                    delete_parent = os.path.join(self.file.storage.location, folder)
            if delete_parent is not None:
                os.rmdir(delete_parent)

    class Meta:
        verbose_name = _('User Asset')
        verbose_name_plural = _('User Assets')


class GiscubeTransaction(models.Model):
    hash = models.CharField(_('Accessed ViewSet'), max_length=32, null=False, blank=False)
    created = models.DateTimeField(_('Access timestamp'), auto_now_add=True, editable=False, null=False, blank=False)
    user = models.CharField(_('User'), max_length=255, null=False, blank=False)
    url = models.CharField(_('URL'), max_length=255, null=False, blank=False)
    request_headers = JSONField(_('request headers'), default=dict)
    request_body = models.TextField(_('request body'), null=True, blank=True)
    response_headers = JSONField(_('request headers'), default=dict)
    response_status_code = models.IntegerField(_('response status code'), null=True, blank=True)
    response_body = models.TextField(_('response body'), null=True, blank=True)
    error = models.TextField(_('error'), null=True, blank=True)
    traceback = models.TextField(_('traceback'), null=True, blank=True)

    @staticmethod
    def purge_old():
        time_delete = {settings.PURGE_GISCUBETRANSACTIONS_UNIT: settings.PURGE_GISCUBETRANSACTIONS_VALUE}
        past = timezone.datetime.today() - timezone.timedelta(**time_delete)
        if settings.USE_TZ:
            past = timezone.make_aware(past)
        GiscubeTransaction.objects.filter(created__lte=past).delete()

    class Meta:
        verbose_name = _('giscube transaction')
        verbose_name_plural = _('giscube transactions')


class Dataset(models.Model):
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='datasets')
    name = models.CharField(_('name'), max_length=50, unique=True)
    title = models.CharField(_('title'), max_length=100, null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)
    keywords = models.CharField(_('keywords'), max_length=200, null=True, blank=True)
    active = models.BooleanField(_('active'), default=True, help_text='Enable/disable usage')
    visible_on_geoportal = models.BooleanField(_('visible on geoportal'), default=False)
    options = models.TextField(
        _('options'), null=True, blank=True, help_text='json format. Ex: {"maxZoom": 20}',
        validators=[validate_options_json_format])
    legend = models.TextField(_('legend'), null=True, blank=True)
    anonymous_view = models.BooleanField(_('anonymous users can view'), default=False)
    authenticated_user_view = models.BooleanField(_('authenticated users can view'), default=False)

    def __str__(self):
        return '%s' % self.title or self.name


RESOURCE_TYPE_CHOICES = [
    ('TMS', 'TMS'),
    ('WMS', 'WMS'),
    ('document', 'Document'),
    ('url', 'URL'),
]


def resource_upload_to(instance, filename):
    return 'dataset/{0}/resource/{1}'.format(instance.dataset.pk, filename)


class Resource(models.Model):
    dataset = models.ForeignKey(Dataset, related_name='resources', on_delete=models.CASCADE)
    type = models.CharField(_('type'), max_length=12, choices=RESOURCE_TYPE_CHOICES)
    name = models.CharField(_('name'), max_length=50)
    description = models.TextField(_('description'), null=True, blank=True)
    title = models.CharField(_('title'), max_length=100, null=True, blank=True)
    path = models.CharField(_('path'), max_length=255, null=True, blank=True)
    url = models.CharField(_('url'), max_length=255, null=True, blank=True)
    file = models.FileField(
        _('file'), max_length=255, null=True, blank=True, upload_to=resource_upload_to, storage=OverwriteStorage())
    layers = models.CharField(_('layers'), max_length=255, null=True, blank=True)
    projection = models.IntegerField(_('projection'), null=True, blank=True, help_text='EPSG code')
    getfeatureinfo_support = models.BooleanField(_('WMS GetFeatureInfo support'), default=True)
    single_image = models.BooleanField(_('use single image'), default=False)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.file:
            folder = os.path.dirname(self.file.name)
            self.file.delete(save=False)
            delete_parent = None
            if isinstance(self.file.storage, FileSystemStorage):
                dirs, files = self.file.storage.listdir(folder)
                if len(files) == 0:
                    delete_parent = os.path.join(self.file.storage.location, folder)
            if delete_parent is not None:
                os.rmdir(delete_parent)

    def __str__(self):
        return '%s' % self.title or self.name


class DatasetGroupPermission(models.Model):
    dataset = models.ForeignKey(Dataset, related_name='group_permissions', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, verbose_name=_('Group'), on_delete=models.CASCADE)
    can_view = models.BooleanField(_('Can view'), default=True)

    def __str__(self):
        return self.group.name

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')


class DatasetUserPermission(models.Model):
    dataset = models.ForeignKey(Dataset, related_name='user_permissions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name=_('User'), on_delete=models.CASCADE)
    can_view = models.BooleanField(_('Can view'), default=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')


class DatasetMetadata(MetadataModelMixin):
    parent = models.OneToOneField(Dataset, on_delete=models.CASCADE, primary_key=True, related_name='metadata')


class MetadataCategory(models.Model):
    code = models.CharField(_('code'), max_length=50, null=False, blank=False, unique=True)
    name = models.CharField(_('name'), max_length=255, null=True, blank=True)

    def __str__(self):
        return '%s' % self.name or self.code

    class Meta:
        verbose_name = _('metadata category')
        verbose_name_plural = _('metadata categories')
