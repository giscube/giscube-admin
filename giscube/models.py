import time

from django.db import models
from django.conf import settings
from django.db import connections
from django.utils.translation import gettext as _


class Category(models.Model):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('Category', null=True, blank=True)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __unicode__(self):
        if self.parent:
            return '%s > %s' % (self.parent.name, self.name)
        else:
            return '%s' % self.name


DB_CONNECTION_ENGINE_CHOICES = [
    ('django.contrib.gis.db.backends.postgis', 'Postgis'),
]


class DBConnection(models.Model):
    alias = models.CharField(max_length=255, null=True, blank=True)
    engine = models.CharField(max_length=255,
                              choices=DB_CONNECTION_ENGINE_CHOICES)
    name = models.CharField(max_length=100, null=False, blank=False)
    user = models.CharField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    host = models.CharField(max_length=100, null=True, blank=True)
    port = models.CharField(max_length=20, null=True, blank=True)

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
            raise ValidationError('DATABASE CONNECTION ERROR')

    def __unicode__(self):
        return '%s' % self.alias or self.name

    class Meta:
        """Meta information."""
        verbose_name = 'Database connection'
        verbose_name_plural = 'Database connections'


class Server(models.Model):
    name = models.CharField(max_length=50, unique=True)
    url = models.URLField(null=True, blank=True)
    token = models.CharField(max_length=255, null=True, blank=True)
    this_server = models.BooleanField(default=False)

    class Meta:
        """Meta information."""
        verbose_name = 'Server connection'
        verbose_name_plural = 'Server connections'

    def __unicode__(self):
        return '%s' % self.name
