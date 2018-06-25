# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json
from slugify import slugify
import shutil

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.gis.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils.translation import gettext as _

from .mixins import BaseLayerMixin, StyleMixin
import layerserver.model_legacy as model_legacy
from giscube.utils import unique_service_directory
from giscube.models import DBConnection
from qgisserver.models import Service


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


class GeoJsonLayer(BaseLayerMixin, StyleMixin, models.Model):
    url = models.CharField(max_length=100, null=True, blank=True)
    data_file = models.FileField(upload_to=geojsonlayer_upload_path,
                                 null=True, blank=True)
    service_path = models.CharField(max_length=255)
    cache_time = models.IntegerField(blank=True, null=True)
    last_fetch_on = models.DateTimeField(null=True, blank=True)
    generated_on = models.DateTimeField(null=True, blank=True)

    @property
    def metadata(self):
        return {
            'description': {
                'title': self.title or '',
                'description': self.description or '',
                'keywords': self.keywords or ''
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

    def __unicode__(self):
        return self.__str__()

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


@receiver(post_save, sender=GeoJsonLayer)
def geojsonlayer_post_save(sender, instance, created, **kwargs):
    if not hasattr(instance, '_disable_post_save'):
        instance._disable_post_save = True
        if instance.data_file:
            path = os.path.join(settings.MEDIA_ROOT, instance.data_file.path)
            data = json.load(open(path))
            data['metadata'] = instance.metadata
            outfile_path = os.path.join(
                settings.MEDIA_ROOT, instance.service_path, 'data.json')
            with open(outfile_path, "wb") as fixed_file:
                fixed_file.write(json.dumps(data))


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

    anonymous_view = models.BooleanField(_('Can view'), default=False)
    anonymous_add = models.BooleanField(_('Can add'), default=False)
    anonymous_update = models.BooleanField(_('Can update'), default=False)
    anonymous_delete = models.BooleanField(_('Can delete'), default=False)

    def __unicode__(self):
        return self.__str__()

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
        instance.pk_field = model._meta.pk.name.split('.')[-1]
        for f in model._meta.fields:
            if type(f) == models.fields.GeometryField:
                instance.geom_field = f.name.split('.')[-1]
                break


@receiver(post_save, sender=DataBaseLayer)
def add_fields(sender, instance, created, **kwargs):
    if created:
        conn = instance.db_connection.get_connection()
        fields = model_legacy.get_fields(conn, instance.table)
        for field in fields:
            db_field = DataBaseLayerField()
            db_field.layer = instance
            db_field.field = field
            db_field.save()


class DataBaseLayerField(models.Model):
    layer = models.ForeignKey(
        DataBaseLayer, null=False, blank=False,
        related_name='fields')
    field = models.CharField(max_length=255, blank=False, null=False)
    alias = models.CharField(max_length=255, blank=True, null=True)
    search = models.BooleanField(default=True)
    fullsearch = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return self.alias or self.field

    class Meta:
        verbose_name = _('Field')
        verbose_name_plural = _('Fields')


class DataBaseLayerReference(models.Model):
    layer = models.ForeignKey(
        DataBaseLayer, null=False, blank=False,
        related_name='references'
        )
    service = models.ForeignKey(
        Service, null=False, blank=False)

    def __unicode__(self):
        return unicode(self.service.title or self.service.name)


    class Meta:
        verbose_name = _('Reference')
        verbose_name_plural = _('References')
        unique_together = ('layer', 'service',)


class DBLayerGroup(models.Model):
    layer = models.ForeignKey(DataBaseLayer, related_name='layer_groups')
    group = models.ForeignKey(Group, verbose_name=_('Group'))
    can_view = models.BooleanField(_('Can view'), default=True)
    can_add = models.BooleanField(_('Can add'), default=True)
    can_update = models.BooleanField(_('Can update'), default=True)
    can_delete = models.BooleanField(_('Can delete'), default=True)

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return self.group.name

    class Meta:
        verbose_name = _('Group')
        verbose_name_plural = _('Groups')


class DBLayerUser(models.Model):
    layer = models.ForeignKey(DataBaseLayer, related_name='layer_users')
    user = models.ForeignKey(User, verbose_name=_('User'), )
    can_view = models.BooleanField(_('Can view'), default=True)
    can_add = models.BooleanField(_('Can add'), default=True)
    can_update = models.BooleanField(_('Can update'), default=True)
    can_delete = models.BooleanField(_('Can delete'), default=True)

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
