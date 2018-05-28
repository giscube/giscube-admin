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

    def db_conf(self):
        db = {}
        db['ENGINE'] = self.engine
        db['NAME'] = self.name
        if self.user:
            db['USER'] = self.user
        if self.password:
            db['PASSWORD'] = self.password
        if self.host:
            db['HOST'] = self.host
        if self.port:
            db['PORT'] = self.port
        return db

    def connection_name(self):
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

    def get_connection(self):
        db_conf = self.db_conf()
        name = self.connection_name()
        if not(name in settings.DATABASES):
            settings.DATABASES[name] = db_conf
        return connections[name]

    def full_clean(self, *args, **kwargs):
        from django.core.validators import ValidationError
        if not self.check_connection():
            raise ValidationError('DATABASE CONNECTION ERROR')

    def __unicode__(self):
        return '%s' % self.alias or self.name


    class Meta:
        """Meta information."""
        verbose_name = 'DBConnection'
        verbose_name_plural = 'DBConnections'
