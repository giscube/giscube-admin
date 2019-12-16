import logging
import os
import time
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import connections, models
from django.forms.models import model_to_dict
from django.utils.translation import gettext as _

from .utils import RecursionException, check_recursion, get_cls


logger = logging.getLogger(__name__)


class Category(models.Model):
    SEPARATOR = ' > '
    name = models.CharField(_('name'), max_length=50)
    parent = models.ForeignKey(
        'Category', verbose_name=_('parent category'), null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    @property
    def title(self):
        if self.parent:
            return '%s%s%s' % (self.parent.name, self.SEPARATOR, self.name)
        else:
            return '%s' % self.name

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

    def table_exists(self, table_name):
        db_conn = self.get_connection()
        cursor = db_conn.cursor()
        try:
            db_conn.introspection.get_table_description(cursor, table_name)
        except Exception:
            return False
        return True

    def fetchall(self, sql):
        rows = []
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            cur.close()
        except Exception:
            rows = ['error']
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
